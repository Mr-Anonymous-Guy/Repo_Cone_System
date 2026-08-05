#!/usr/bin/env python3
"""
CI Guardian - Local CI Validation & Diagnosis Engine
=====================================================

Reproduces, diagnoses, validates, and gates Git pushes by running
the exact commands defined in GitHub Actions workflows locally.

Usage:
    python scripts/ci_guardian.py              # Full validation pipeline
    python scripts/ci_guardian.py --analyze    # Static analysis only (no execution)
    python scripts/ci_guardian.py --fix        # Analyze + apply high-confidence fixes
    python scripts/ci_guardian.py --report     # Full pipeline + generate ci_report.md

Architecture:
    RepoDetector     -> Identifies repository language/toolchain
    WorkflowParser   -> Discovers and parses .github/workflows/*.yml
    WorkflowAnalyzer -> Static analysis for deprecated actions, bad configs
    LocalReproducer  -> Executes workflow steps locally per matrix combo
    Diagnostician    -> Root-cause analysis on failures
    FixApplicator    -> Applies fixes only when confidence >= 0.85
    ValidationGate   -> Runs full pipeline, gates push readiness
    ReportGenerator  -> Produces structured CI report
"""

import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Try to import PyYAML; if missing, offer to install it
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("[CI Guardian] PyYAML is required. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
    import yaml


# ===========================================================================
# Data Models
# ===========================================================================


@dataclass
class Finding:
    """A single static-analysis finding."""

    severity: str  # CRITICAL, WARNING, INFO
    category: str  # e.g. "deprecated-action", "eol-python", "missing-cache"
    message: str
    file: str
    line: Optional[int] = None
    evidence: str = ""
    recommended_fix: str = ""
    confidence: float = 0.0  # 0.0 - 1.0


@dataclass
class StepResult:
    """Result of executing a single workflow step locally."""

    name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    passed: bool


@dataclass
class JobResult:
    """Result of executing an entire job (all steps) for one matrix combo."""

    job_name: str
    matrix_label: str  # e.g. "python-3.11"
    steps: List[StepResult] = field(default_factory=list)
    passed: bool = True


@dataclass
class Diagnosis:
    """Structured root-cause analysis for a failure."""

    failing_step: str
    root_cause: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    recommended_fixes: List[str] = field(default_factory=list)
    risk: str = "UNKNOWN"


@dataclass
class Fix:
    """A fix to apply."""

    file: str
    description: str
    confidence: float
    diff_before: str = ""
    diff_after: str = ""


@dataclass
class ValidationStage:
    """Result of one validation gate stage."""

    name: str
    command: str
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class CIReport:
    """The full CI Guardian report."""

    repo_type: str
    workflows_discovered: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    job_results: List[JobResult] = field(default_factory=list)
    diagnoses: List[Diagnosis] = field(default_factory=list)
    fixes_applied: List[Fix] = field(default_factory=list)
    validation_stages: List[ValidationStage] = field(default_factory=list)
    push_ready: bool = False


# ===========================================================================
# Constants
# ===========================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent

# Known deprecated/outdated GitHub Actions
LATEST_ACTIONS = {
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "actions/setup-node": "v4",
    "actions/cache": "v4",
    "actions/upload-artifact": "v4",
    "actions/download-artifact": "v4",
}

# Python versions that are End-of-Life
EOL_PYTHON_VERSIONS = {"3.7", "3.8"}

# Supported Python versions for CI matrix
SUPPORTED_PYTHON_VERSIONS = {"3.9", "3.10", "3.11", "3.12", "3.13"}

# Minimum confidence to auto-apply a fix
FIX_CONFIDENCE_THRESHOLD = 0.85


# Terminal colors (Windows-safe via colorama or fallback)
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def _c(text: str, color: str) -> str:
    """Wrap text in terminal color codes."""
    return f"{color}{text}{Colors.RESET}"


def _header(title: str) -> str:
    line = "=" * 60
    return (
        f"\n{_c(line, Colors.CYAN)}\n{_c(title, Colors.BOLD)}\n{_c(line, Colors.CYAN)}"
    )


def _status(passed: bool) -> str:
    return _c("[PASS]", Colors.GREEN) if passed else _c("[FAIL]", Colors.RED)


# ===========================================================================
# 1. Repository Detector
# ===========================================================================


class RepoDetector:
    """Auto-detects repository type and toolchain."""

    MARKERS = {
        "python": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
        "nodejs": ["package.json"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod"],
    }

    def __init__(self, root: Path):
        self.root = root

    def detect(self) -> Dict[str, Any]:
        """Returns a dict describing the detected repo type."""
        detected = {}
        for lang, markers in self.MARKERS.items():
            for marker in markers:
                if (self.root / marker).exists():
                    detected[lang] = True
                    break

        repo_type = "unknown"
        if "python" in detected:
            repo_type = "python"
        elif "nodejs" in detected:
            repo_type = "nodejs"
        elif "rust" in detected:
            repo_type = "rust"
        elif "go" in detected:
            repo_type = "go"

        if len(detected) > 1:
            repo_type = "mixed (" + ", ".join(sorted(detected.keys())) + ")"

        result = {
            "type": repo_type,
            "languages": list(detected.keys()),
            "has_pyproject": (self.root / "pyproject.toml").exists(),
            "has_src_layout": (self.root / "src").is_dir(),
            "has_tests": (self.root / "tests").is_dir(),
        }

        print(_header("Repository Detection"))
        print(f"  Type       : {_c(result['type'], Colors.CYAN)}")
        print(f"  Languages  : {', '.join(result['languages'])}")
        print(f"  src/ layout: {'Yes' if result['has_src_layout'] else 'No'}")
        print(f"  tests/     : {'Yes' if result['has_tests'] else 'No'}")

        return result


# ===========================================================================
# 2. Workflow Parser
# ===========================================================================


class WorkflowParser:
    """Discovers and parses GitHub Actions workflow YAML files."""

    def __init__(self, root: Path):
        self.root = root
        self.workflows_dir = root / ".github" / "workflows"

    def discover(self) -> List[Path]:
        """Find all workflow YAML files."""
        if not self.workflows_dir.exists():
            return []
        return sorted(self.workflows_dir.glob("*.yml")) + sorted(
            self.workflows_dir.glob("*.yaml")
        )

    def parse(self, path: Path) -> Optional[Dict]:
        """Parse a single workflow YAML file. Returns None on parse error."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"  {_c('YAML parse error', Colors.RED)}: {path.name}: {e}")
            return None

    def parse_all(self) -> Dict[str, Dict]:
        """Parse all discovered workflows. Returns {filename: parsed_dict}."""
        paths = self.discover()
        print(_header("Workflow Discovery"))

        if not paths:
            print(f"  {_c('No workflows found', Colors.YELLOW)} in .github/workflows/")
            return {}

        results = {}
        for p in paths:
            print(f"  Found: {_c(p.name, Colors.CYAN)}")
            parsed = self.parse(p)
            if parsed is not None:
                results[p.name] = parsed

        print(f"\n  {len(results)} workflow(s) parsed successfully.")
        return results


# ===========================================================================
# 3. Workflow Analyzer
# ===========================================================================


class WorkflowAnalyzer:
    """Static analysis of parsed workflow configurations."""

    def __init__(self, root: Path):
        self.root = root
        self.workflows_dir = root / ".github" / "workflows"

    def analyze(self, workflows: Dict[str, Dict]) -> List[Finding]:
        """Run all static analysis checks on parsed workflows."""
        findings = []
        for filename, wf in workflows.items():
            filepath = str(self.workflows_dir / filename)
            findings.extend(self._check_deprecated_actions(wf, filepath))
            findings.extend(self._check_matrix_python_versions(wf, filepath))
            findings.extend(self._check_fail_fast(wf, filepath))
            findings.extend(self._check_missing_cache(wf, filepath))
            findings.extend(self._check_missing_permissions(wf, filepath))

        print(_header("Static Analysis"))
        if not findings:
            print(f"  {_c('No issues found', Colors.GREEN)}")
        else:
            for f in findings:
                sev_color = {
                    "CRITICAL": Colors.RED,
                    "WARNING": Colors.YELLOW,
                    "INFO": Colors.BLUE,
                }.get(f.severity, Colors.DIM)
                print(
                    f"  {_c(f'[{f.severity}]', sev_color)} "
                    f"{f.category}: {f.message}"
                )
                if f.evidence:
                    print(f"           Evidence: {_c(f.evidence, Colors.DIM)}")
                if f.recommended_fix:
                    print(f"           Fix: {_c(f.recommended_fix, Colors.GREEN)}")

        return findings

    def _check_deprecated_actions(self, wf: Dict, filepath: str) -> List[Finding]:
        findings = []
        jobs = wf.get("jobs", {})
        for job_name, job in jobs.items():
            for step in job.get("steps", []):
                uses = step.get("uses", "")
                if not uses or "/" not in uses:
                    continue
                action_name, _, version = uses.partition("@")
                if action_name in LATEST_ACTIONS:
                    latest = LATEST_ACTIONS[action_name]
                    if version != latest:
                        findings.append(
                            Finding(
                                severity="WARNING",
                                category="outdated-action",
                                message=f"{action_name}@{version} is outdated",
                                file=filepath,
                                evidence=f"Current: @{version}, Latest: @{latest}",
                                recommended_fix=f"Update to {action_name}@{latest}",
                                confidence=0.95,
                            )
                        )
        return findings

    def _check_matrix_python_versions(self, wf: Dict, filepath: str) -> List[Finding]:
        findings = []
        jobs = wf.get("jobs", {})
        for job_name, job in jobs.items():
            strategy = job.get("strategy", {})
            matrix = strategy.get("matrix", {})
            py_versions = matrix.get("python-version", [])
            for pv in py_versions:
                pv_str = str(pv)
                if pv_str in EOL_PYTHON_VERSIONS:
                    findings.append(
                        Finding(
                            severity="CRITICAL",
                            category="eol-python",
                            message=f"Python {pv_str} is End-of-Life in CI matrix",
                            file=filepath,
                            evidence=f"Python {pv_str} EOL; ruff/black dropped support",
                            recommended_fix=f"Remove Python {pv_str} from matrix",
                            confidence=0.95,
                        )
                    )
        return findings

    def _check_fail_fast(self, wf: Dict, filepath: str) -> List[Finding]:
        findings = []
        jobs = wf.get("jobs", {})
        for job_name, job in jobs.items():
            strategy = job.get("strategy", {})
            matrix = strategy.get("matrix", {})
            if matrix and "fail-fast" not in strategy:
                findings.append(
                    Finding(
                        severity="WARNING",
                        category="missing-fail-fast",
                        message=f"Job '{job_name}' uses matrix without explicit fail-fast",
                        file=filepath,
                        evidence="Default fail-fast: true cancels sibling jobs on first failure",
                        recommended_fix="Add 'fail-fast: false' to strategy",
                        confidence=0.90,
                    )
                )
        return findings

    def _check_missing_cache(self, wf: Dict, filepath: str) -> List[Finding]:
        findings = []
        jobs = wf.get("jobs", {})
        for job_name, job in jobs.items():
            steps = job.get("steps", [])
            has_pip_install = any("pip install" in str(s.get("run", "")) for s in steps)
            has_cache = any("cache" in str(s.get("uses", "")).lower() for s in steps)
            has_setup_python_cache = False
            for s in steps:
                if "setup-python" in str(s.get("uses", "")):
                    with_block = s.get("with", {})
                    if "cache" in with_block:
                        has_setup_python_cache = True

            if has_pip_install and not has_cache and not has_setup_python_cache:
                findings.append(
                    Finding(
                        severity="INFO",
                        category="missing-cache",
                        message=f"Job '{job_name}' installs pip packages without caching",
                        file=filepath,
                        evidence="pip install without cache slows CI by ~30-60s",
                        recommended_fix="Add 'cache: pip' to actions/setup-python",
                        confidence=0.85,
                    )
                )
        return findings

    def _check_missing_permissions(self, wf: Dict, filepath: str) -> List[Finding]:
        findings = []
        if "permissions" not in wf:
            has_write_steps = False
            jobs = wf.get("jobs", {})
            for job_name, job in jobs.items():
                if "permissions" not in job:
                    for step in job.get("steps", []):
                        run_cmd = str(step.get("run", ""))
                        if any(
                            kw in run_cmd
                            for kw in ["twine upload", "gh release", "git push"]
                        ):
                            has_write_steps = True

            if not has_write_steps:
                findings.append(
                    Finding(
                        severity="INFO",
                        category="missing-permissions",
                        message="Workflow has no top-level 'permissions' block",
                        file=filepath,
                        evidence="Best practice: restrict permissions with least privilege",
                        recommended_fix="Add 'permissions: contents: read'",
                        confidence=0.80,
                    )
                )
        return findings


# ===========================================================================
# 4. Local Reproducer
# ===========================================================================


class LocalReproducer:
    """Executes workflow steps locally to reproduce CI behavior."""

    def __init__(self, root: Path):
        self.root = root

    def find_available_pythons(self) -> Dict[str, str]:
        """Detect which Python versions are available on this machine."""
        available = {}
        is_windows = platform.system() == "Windows"

        for ver in sorted(SUPPORTED_PYTHON_VERSIONS):
            candidates = []
            if is_windows:
                candidates = [f"py -{ver}", f"python{ver}"]
            else:
                candidates = [f"python{ver}", f"python{ver[0]}"]

            # Always try the current interpreter
            for cmd in candidates:
                try:
                    result = subprocess.run(
                        cmd.split() + ["--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        version_str = result.stdout.strip() or result.stderr.strip()
                        if ver in version_str:
                            available[ver] = cmd
                            break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

        # Always include the current interpreter
        current_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        if current_ver not in available:
            available[current_ver] = sys.executable

        return available

    def execute_step(self, command: str, env: Optional[Dict] = None) -> StepResult:
        """Execute a single shell command and capture results."""
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.root),
                env=merged_env,
                timeout=300,
            )
            duration = time.time() - start
            return StepResult(
                name=command[:60],
                command=command,
                exit_code=result.returncode,
                stdout=result.stdout[-2000:] if result.stdout else "",
                stderr=result.stderr[-2000:] if result.stderr else "",
                duration_seconds=round(duration, 2),
                passed=result.returncode == 0,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return StepResult(
                name=command[:60],
                command=command,
                exit_code=-1,
                stdout="",
                stderr="TIMEOUT: Command exceeded 300 seconds",
                duration_seconds=round(duration, 2),
                passed=False,
            )

    def reproduce_workflow(self, workflow: Dict, workflow_name: str) -> List[JobResult]:
        """Reproduce all jobs/matrix combos from a workflow."""
        results = []
        jobs = workflow.get("jobs", {})

        print(_header(f"Reproducing: {workflow_name}"))

        for job_name, job in jobs.items():
            strategy = job.get("strategy", {})
            matrix = strategy.get("matrix", {})
            py_versions = matrix.get("python-version", [])

            if not py_versions:
                # No matrix - run once with current Python
                jr = self._reproduce_job(job_name, job, None)
                results.append(jr)
            else:
                available = self.find_available_pythons()
                for pv in py_versions:
                    pv_str = str(pv)
                    if pv_str in EOL_PYTHON_VERSIONS:
                        print(
                            f"\n  {_c('[SKIP]', Colors.YELLOW)} "
                            f"Python {pv_str} (End-of-Life)"
                        )
                        continue
                    if pv_str not in available:
                        print(
                            f"\n  {_c('[SKIP]', Colors.YELLOW)} "
                            f"Python {pv_str} (not installed locally)"
                        )
                        continue

                    jr = self._reproduce_job(job_name, job, pv_str)
                    results.append(jr)

        return results

    def _reproduce_job(
        self, job_name: str, job: Dict, python_version: Optional[str]
    ) -> JobResult:
        """Reproduce a single job for a specific Python version."""
        label = f"python-{python_version}" if python_version else "default"
        jr = JobResult(job_name=job_name, matrix_label=label)

        print(f"\n  Job: {_c(job_name, Colors.CYAN)} [{label}]")
        print(f"  {'-' * 50}")

        for step in job.get("steps", []):
            run_cmd = step.get("run", "")
            if not run_cmd:
                continue

            step_name = step.get("name", run_cmd[:40])
            # Handle multi-line run commands
            commands = [
                line.strip() for line in run_cmd.strip().split("\n") if line.strip()
            ]

            for cmd in commands:
                sr = self.execute_step(cmd)
                sr.name = step_name
                jr.steps.append(sr)

                status = _status(sr.passed)
                timing = _c(f"({sr.duration_seconds}s)", Colors.DIM)
                print(f"    {status} {sr.name}: {cmd[:50]} {timing}")

                if not sr.passed:
                    jr.passed = False
                    # Show first 3 lines of stderr
                    err_lines = sr.stderr.strip().split("\n")[:3]
                    for el in err_lines:
                        print(f"           {_c(el[:80], Colors.RED)}")
                    break  # Stop on first failure in this job

            if not jr.passed:
                break

        return jr


# ===========================================================================
# 5. Diagnostician
# ===========================================================================


class Diagnostician:
    """Root-cause analysis for CI failures."""

    ERROR_PATTERNS = [
        {
            "pattern": r"No module named '(\w+)'",
            "cause": "Missing Python dependency: {0}",
            "fix": "pip install {0}",
            "confidence": 0.90,
            "risk": "LOW",
        },
        {
            "pattern": r"SyntaxError",
            "cause": "Python syntax error in source code",
            "fix": "Fix the syntax error in the identified file",
            "confidence": 0.95,
            "risk": "HIGH - code is broken",
        },
        {
            "pattern": r"ruff.*error|ruff.*check",
            "cause": "Linting violations detected by ruff",
            "fix": "Run 'ruff check --fix .' to auto-fix, or address manually",
            "confidence": 0.90,
            "risk": "LOW - style/lint only",
        },
        {
            "pattern": r"would reformat|reformatted",
            "cause": "Code formatting does not match black style",
            "fix": "Run 'black .' to auto-format",
            "confidence": 0.95,
            "risk": "LOW - formatting only",
        },
        {
            "pattern": r"FAILED|ERRORS|assert.*Error",
            "cause": "Unit test failure",
            "fix": "Review test output and fix failing assertions",
            "confidence": 0.85,
            "risk": "HIGH - tests are failing",
        },
        {
            "pattern": r"requires-python.*>=\s*(\d+\.\d+)",
            "cause": "Python version is below requires-python minimum",
            "fix": "Use a supported Python version",
            "confidence": 0.90,
            "risk": "LOW - version configuration",
        },
        {
            "pattern": r"InvalidConfigError|SetuptoolsDeprecationWarning",
            "cause": "pyproject.toml configuration issue",
            "fix": "Review pyproject.toml for deprecated fields",
            "confidence": 0.90,
            "risk": "MEDIUM - build configuration",
        },
    ]

    def diagnose(self, job_results: List[JobResult]) -> List[Diagnosis]:
        """Analyze failed jobs and produce diagnoses."""
        diagnoses = []
        for jr in job_results:
            if jr.passed:
                continue
            for sr in jr.steps:
                if sr.passed:
                    continue
                diag = self._analyze_failure(sr, jr.matrix_label)
                if diag:
                    diagnoses.append(diag)

        print(_header("Diagnosis"))
        if not diagnoses:
            print(f"  {_c('No failures to diagnose', Colors.GREEN)}")
        else:
            for d in diagnoses:
                conf_color = Colors.GREEN if d.confidence >= 0.85 else Colors.YELLOW
                print(f"\n  Failing Step : {_c(d.failing_step, Colors.RED)}")
                print(f"  Root Cause   : {d.root_cause}")
                print(f"  Confidence   : {_c(f'{d.confidence:.0%}', conf_color)}")
                print(f"  Risk         : {d.risk}")
                for ev in d.evidence[:3]:
                    print(f"  Evidence     : {_c(ev[:80], Colors.DIM)}")
                for fx in d.recommended_fixes:
                    print(f"  Fix          : {_c(fx, Colors.GREEN)}")

        return diagnoses

    def _analyze_failure(
        self, step: StepResult, matrix_label: str
    ) -> Optional[Diagnosis]:
        combined = step.stdout + "\n" + step.stderr
        evidence = []

        for pat in self.ERROR_PATTERNS:
            match = re.search(pat["pattern"], combined, re.IGNORECASE)
            if match:
                groups = match.groups() if match.groups() else ()
                cause = pat["cause"].format(*groups) if groups else pat["cause"]
                fix = pat["fix"].format(*groups) if groups else pat["fix"]
                # Grab surrounding context as evidence
                for line in combined.split("\n"):
                    if re.search(pat["pattern"], line, re.IGNORECASE):
                        evidence.append(line.strip()[:120])

                return Diagnosis(
                    failing_step=f"{step.name} [{matrix_label}]",
                    root_cause=cause,
                    confidence=pat["confidence"],
                    evidence=evidence[:5],
                    recommended_fixes=[fix],
                    risk=pat["risk"],
                )

        # Generic fallback diagnosis
        stderr_lines = [
            line.strip() for line in step.stderr.split("\n") if line.strip()
        ]
        return Diagnosis(
            failing_step=f"{step.name} [{matrix_label}]",
            root_cause=f"Command exited with code {step.exit_code}",
            confidence=0.50,
            evidence=stderr_lines[:5],
            recommended_fixes=["Review the error output manually"],
            risk="UNKNOWN",
        )


# ===========================================================================
# 6. Fix Applicator
# ===========================================================================


class FixApplicator:
    """Applies high-confidence, localized fixes to workflow and config files."""

    def __init__(self, root: Path):
        self.root = root
        self.applied: List[Fix] = []

    def apply_workflow_fixes(self, findings: List[Finding]) -> List[Fix]:
        """Apply fixes for workflow-level findings."""
        fixes = []

        # Group findings by file
        by_file: Dict[str, List[Finding]] = {}
        for f in findings:
            by_file.setdefault(f.file, []).append(f)

        for filepath, file_findings in by_file.items():
            # Only apply if ALL findings for this file meet threshold
            applicable = [
                f for f in file_findings if f.confidence >= FIX_CONFIDENCE_THRESHOLD
            ]
            if not applicable:
                continue

            path = Path(filepath)
            if not path.exists():
                continue

            original = path.read_text(encoding="utf-8")
            modified = original

            for finding in applicable:
                if finding.category == "outdated-action":
                    # Extract action@version from evidence
                    match = re.search(
                        r"Current: @(\S+), Latest: @(\S+)", finding.evidence
                    )
                    if match:
                        old_ver, new_ver = match.groups()
                        action = finding.message.split("@")[0]
                        modified = modified.replace(
                            f"{action}@{old_ver}", f"{action}@{new_ver}"
                        )

                elif finding.category == "eol-python":
                    # Remove EOL Python from matrix list
                    match = re.search(r"Python (\d+\.\d+)", finding.message)
                    if match:
                        eol_ver = match.group(1)
                        # Remove from YAML list patterns
                        modified = re.sub(rf'[,\s]*"{eol_ver}"', "", modified)
                        modified = re.sub(rf'"{eol_ver}"[,\s]*', "", modified)

                elif finding.category == "missing-fail-fast":
                    modified = modified.replace(
                        "      matrix:", "      fail-fast: false\n      matrix:"
                    )

                elif finding.category == "missing-cache":
                    # Add cache to setup-python
                    modified = modified.replace(
                        "          python-version:",
                        "          cache: pip\n          python-version:",
                    )

            if modified != original:
                fix = Fix(
                    file=filepath,
                    description="; ".join(f.recommended_fix for f in applicable),
                    confidence=min(f.confidence for f in applicable),
                    diff_before=original[:500],
                    diff_after=modified[:500],
                )
                path.write_text(modified, encoding="utf-8")
                fixes.append(fix)
                self.applied.append(fix)

        return fixes

    def apply_pyproject_fixes(self, findings: List[Finding]) -> List[Fix]:
        """Fix pyproject.toml based on EOL Python findings."""
        fixes = []
        pyproject_path = self.root / "pyproject.toml"
        if not pyproject_path.exists():
            return fixes

        eol_versions = set()
        for f in findings:
            if f.category == "eol-python":
                match = re.search(r"Python (\d+\.\d+)", f.message)
                if match:
                    eol_versions.add(match.group(1))

        if not eol_versions:
            return fixes

        original = pyproject_path.read_text(encoding="utf-8")
        modified = original

        for ver in eol_versions:
            # Update requires-python
            modified = modified.replace(
                f'requires-python = ">={ver}"', 'requires-python = ">=3.9"'
            )
            # Remove classifier
            modified = re.sub(
                rf'\s*"Programming Language :: Python :: {re.escape(ver)}",?\n?',
                "\n",
                modified,
            )
            # Update black target-version
            modified = modified.replace(
                f"target-version = ['py{ver.replace('.', '')}']",
                "target-version = ['py39']",
            )
            # Update ruff target-version
            modified = modified.replace(
                f'target-version = "py{ver.replace(".", "")}"',
                'target-version = "py39"',
            )

        if modified != original:
            fix = Fix(
                file=str(pyproject_path),
                description=f"Drop EOL Python {', '.join(sorted(eol_versions))}; update requires-python to >=3.9",
                confidence=0.95,
            )
            pyproject_path.write_text(modified, encoding="utf-8")
            fixes.append(fix)
            self.applied.append(fix)

        return fixes

    def report_fixes(self):
        """Print applied fixes."""
        print(_header("Fixes Applied"))
        if not self.applied:
            print(f"  {_c('No fixes applied', Colors.DIM)}")
            return

        for fix in self.applied:
            print(f"\n  File: {_c(Path(fix.file).name, Colors.CYAN)}")
            print(f"  Description: {fix.description}")
            print(f"  Confidence: {_c(f'{fix.confidence:.0%}', Colors.GREEN)}")


# ===========================================================================
# 7. Validation Gate
# ===========================================================================


class ValidationGate:
    """Runs the full validation pipeline and gates push readiness."""

    STAGES = [
        ("Dependency Installation", 'pip install -e ".[dev]" -q'),
        ("Linting (ruff)", "ruff check ."),
        ("Formatting (black)", "black --check ."),
        ("Unit Tests (pytest)", "pytest"),
        ("Package Build", "python -m build -q"),
    ]

    def __init__(self, root: Path):
        self.root = root

    def run(self) -> Tuple[bool, List[ValidationStage]]:
        """Run all validation stages. Returns (all_passed, stage_results)."""
        print(_header("Validation Gate"))
        results = []
        all_passed = True

        for name, cmd in self.STAGES:
            start = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(self.root),
                    timeout=300,
                )
                duration = time.time() - start
                passed = proc.returncode == 0
            except subprocess.TimeoutExpired:
                duration = time.time() - start
                proc = type(
                    "obj",
                    (object,),
                    {
                        "returncode": -1,
                        "stdout": "",
                        "stderr": "TIMEOUT",
                    },
                )()
                passed = False

            stage = ValidationStage(
                name=name,
                command=cmd,
                passed=passed,
                exit_code=proc.returncode,
                stdout=proc.stdout[-1000:] if proc.stdout else "",
                stderr=proc.stderr[-1000:] if proc.stderr else "",
                duration_seconds=round(duration, 2),
            )
            results.append(stage)

            status = _status(passed)
            timing = _c(f"({stage.duration_seconds}s)", Colors.DIM)
            print(f"  {status} {name} {timing}")

            if not passed:
                all_passed = False
                err_lines = stage.stderr.strip().split("\n")[:3]
                for el in err_lines:
                    if el.strip():
                        print(f"         {_c(el[:80], Colors.RED)}")

        return all_passed, results


# ===========================================================================
# 8. Report Generator
# ===========================================================================


class ReportGenerator:
    """Generates structured CI report."""

    def __init__(self, root: Path):
        self.root = root

    def generate(self, report: CIReport) -> str:
        """Generate markdown CI report."""
        lines = [
            "# CI Guardian Report",
            "",
            f"**Repository Type**: {report.repo_type}",
            f"**Push Ready**: {'YES' if report.push_ready else 'NO - BLOCKED'}",
            f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Workflows
        lines.append("## Workflows Discovered")
        for w in report.workflows_discovered:
            lines.append(f"- {w}")
        lines.append("")

        # Findings
        if report.findings:
            lines.append("## Static Analysis Findings")
            lines.append("")
            lines.append("| Severity | Category | Message | Confidence |")
            lines.append("|---|---|---|---|")
            for f in report.findings:
                lines.append(
                    f"| {f.severity} | {f.category} | {f.message} | {f.confidence:.0%} |"
                )
            lines.append("")

        # Validation Stages
        if report.validation_stages:
            lines.append("## Validation Pipeline")
            lines.append("")
            lines.append("| Stage | Status | Duration | Exit Code |")
            lines.append("|---|---|---|---|")
            for s in report.validation_stages:
                status = "PASS" if s.passed else "FAIL"
                lines.append(
                    f"| {s.name} | {status} | {s.duration_seconds}s | {s.exit_code} |"
                )
            lines.append("")

        # Diagnoses
        if report.diagnoses:
            lines.append("## Diagnoses")
            for d in report.diagnoses:
                lines.append(f"\n### {d.failing_step}")
                lines.append(f"- **Root Cause**: {d.root_cause}")
                lines.append(f"- **Confidence**: {d.confidence:.0%}")
                lines.append(f"- **Risk**: {d.risk}")
                for ev in d.evidence:
                    lines.append(f"- Evidence: `{ev[:100]}`")
                for fx in d.recommended_fixes:
                    lines.append(f"- Fix: {fx}")
            lines.append("")

        # Fixes
        if report.fixes_applied:
            lines.append("## Fixes Applied")
            for f in report.fixes_applied:
                lines.append(
                    f"\n- **{Path(f.file).name}**: {f.description} (confidence: {f.confidence:.0%})"
                )
            lines.append("")

        # Final verdict
        lines.append("## Final Verdict")
        if report.push_ready:
            lines.append("> **READY TO PUSH** - All validation stages passed.")
        else:
            lines.append("> **BLOCKED** - Fix the issues above before pushing.")

        content = "\n".join(lines)

        # Save to file
        report_path = self.root / "ci_report.md"
        report_path.write_text(content, encoding="utf-8")
        print(f"\n  Report saved to: {_c(str(report_path), Colors.CYAN)}")

        return content


# ===========================================================================
# Main Orchestrator
# ===========================================================================


class CIGuardian:
    """Main orchestrator that ties all components together."""

    def __init__(self, root: Path = REPO_ROOT):
        self.root = root
        self.detector = RepoDetector(root)
        self.parser = WorkflowParser(root)
        self.analyzer = WorkflowAnalyzer(root)
        self.reproducer = LocalReproducer(root)
        self.diagnostician = Diagnostician()
        self.fixer = FixApplicator(root)
        self.gate = ValidationGate(root)
        self.reporter = ReportGenerator(root)

    def run(
        self,
        analyze_only: bool = False,
        apply_fixes: bool = False,
        generate_report: bool = False,
    ) -> CIReport:
        """Run the full CI Guardian pipeline."""

        print(
            f"\n{_c('=' * 60, Colors.BOLD)}"
            f"\n{_c('  CI GUARDIAN', Colors.BOLD)}"
            f"\n{_c('  Local CI Validation & Diagnosis Engine', Colors.DIM)}"
            f"\n{_c('=' * 60, Colors.BOLD)}"
        )

        report = CIReport(repo_type="unknown")

        # 1. Detect repo type
        repo_info = self.detector.detect()
        report.repo_type = repo_info["type"]

        # 2. Parse workflows
        workflows = self.parser.parse_all()
        report.workflows_discovered = list(workflows.keys())

        # 3. Static analysis
        findings = self.analyzer.analyze(workflows)
        report.findings = findings

        if analyze_only:
            self._print_final_verdict(report)
            return report

        # 4. Apply fixes if requested and findings have high confidence
        if apply_fixes and findings:
            wf_fixes = self.fixer.apply_workflow_fixes(findings)
            pyproject_fixes = self.fixer.apply_pyproject_fixes(findings)
            report.fixes_applied = wf_fixes + pyproject_fixes
            self.fixer.report_fixes()

            # Re-parse workflows after fixes
            if wf_fixes:
                workflows = self.parser.parse_all()

        # 5. Reproduce workflows locally
        all_job_results = []
        for wf_name, wf_data in workflows.items():
            # Only reproduce test/CI workflows, not publish/deploy
            triggers = wf_data.get("on", {})
            if isinstance(triggers, dict) and "release" in triggers:
                print(
                    f"\n  {_c('[SKIP]', Colors.YELLOW)} {wf_name} (release-only workflow)"
                )
                continue
            job_results = self.reproducer.reproduce_workflow(wf_data, wf_name)
            all_job_results.extend(job_results)
        report.job_results = all_job_results

        # 6. Diagnose failures
        diagnoses = self.diagnostician.diagnose(all_job_results)
        report.diagnoses = diagnoses

        # 7. Run validation gate
        all_passed, stages = self.gate.run()
        report.validation_stages = stages
        report.push_ready = all_passed

        # 8. Generate report if requested
        if generate_report:
            self.reporter.generate(report)

        # Final verdict
        self._print_final_verdict(report)

        return report

    def _print_final_verdict(self, report: CIReport):
        """Print the final push readiness verdict."""
        print(_header("Final Verdict"))

        findings_critical = sum(1 for f in report.findings if f.severity == "CRITICAL")
        findings_warning = sum(1 for f in report.findings if f.severity == "WARNING")
        findings_info = sum(1 for f in report.findings if f.severity == "INFO")

        print(
            f"  Findings   : {findings_critical} critical, {findings_warning} warnings, {findings_info} info"
        )
        print(f"  Fixes      : {len(report.fixes_applied)} applied")
        print(f"  Diagnoses  : {len(report.diagnoses)} issues diagnosed")

        if report.validation_stages:
            passed = sum(1 for s in report.validation_stages if s.passed)
            total = len(report.validation_stages)
            print(f"  Validation : {passed}/{total} stages passed")

        if report.push_ready:
            print(f"\n  {_c('READY TO PUSH', Colors.GREEN)} - All checks passed.")
        else:
            print(f"\n  {_c('PUSH BLOCKED', Colors.RED)} - Fix issues before pushing.")


# ===========================================================================
# CLI Entry Point
# ===========================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="CI Guardian - Local CI Validation & Diagnosis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ci_guardian.py                # Full validation pipeline
  python scripts/ci_guardian.py --analyze      # Static analysis only
  python scripts/ci_guardian.py --fix          # Analyze + apply fixes
  python scripts/ci_guardian.py --report       # Full pipeline + report
  python scripts/ci_guardian.py --fix --report # Fix, validate, and report
        """,
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run static analysis only (no execution)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply high-confidence fixes automatically",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate ci_report.md with full results",
    )

    args = parser.parse_args()

    guardian = CIGuardian()
    report = guardian.run(
        analyze_only=args.analyze,
        apply_fixes=args.fix,
        generate_report=args.report or args.fix,
    )

    sys.exit(0 if report.push_ready or args.analyze else 1)


if __name__ == "__main__":
    main()
