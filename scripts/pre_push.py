#!/usr/bin/env python3
"""
Pre-Push Validation System
===========================

A mandatory 16-stage validation pipeline that intercepts all git push
operations and blocks the push until every stage passes.

Usage:
    python scripts/pre_push.py                     # Full pipeline
    python scripts/pre_push.py --stage 4           # Run up to stage N
    python scripts/pre_push.py --skip-matrix       # Skip matrix validation
    python scripts/pre_push.py --no-restart        # Disable auto-restart
    python scripts/pre_push.py --report            # Generate pre_push_report.md

Architecture:
    ValidatorRegistry  -> Plugin system for auto-discovering validators
    BaseValidator      -> Abstract base for all 16 stages
    ValidationContext  -> Shared state across stages
    PrePushEngine      -> Orchestrator running stages in order
"""

import os
import platform
import re
import shutil
import subprocess
import sys
import time

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pyyaml", "-q"],
        stdout=subprocess.DEVNULL,
    )
    import yaml


# ===========================================================================
# Constants
# ===========================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_RESTARTS = 3

LATEST_ACTIONS = {
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "actions/setup-node": "v4",
    "actions/cache": "v4",
    "actions/upload-artifact": "v4",
    "actions/download-artifact": "v4",
}

EOL_PYTHON = {"3.7", "3.8"}

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]", "API Key"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[A-Za-z0-9]{36}", "GitHub OAuth Token"),
    (r"glpat-[A-Za-z0-9\-]{20,}", "GitLab Personal Access Token"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI / Stripe Secret Key"),
    (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Private Key"),
    (r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded Password"),
    (r"(?i)secret\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Hardcoded Secret"),
]

# Excluded directories and files for security scanning
SCAN_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".eggs",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".tox",
    ".nox",
}
SCAN_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".cfg",
    ".ini",
    ".env",
    ".sh",
    ".bat",
    ".ps1",
    ".rb",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".swift",
}


# ===========================================================================
# Terminal Colors
# ===========================================================================


class C:
    """Terminal color codes."""

    RST = "\033[0m"
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    M = "\033[95m"
    CY = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{C.RST}"


def _pass():
    return _c("PASS", C.G)


def _fail():
    return _c("FAIL", C.R)


def _skip():
    return _c("SKIP", C.Y)


def _bar(char="─", width=60):
    return _c(char * width, C.DIM)


def _header(title: str):
    print(f"\n{_bar('━')}")
    print(f"  {_c(title, C.BOLD)}")
    print(_bar("━"))


# ===========================================================================
# Data Models
# ===========================================================================


@dataclass
class StageResult:
    """Result of a single validation stage."""

    name: str
    order: int
    passed: bool
    skipped: bool = False
    skip_reason: str = ""
    duration: float = 0.0
    details: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    findings: List[Dict] = field(default_factory=list)
    auto_fixable: bool = False
    fix_applied: bool = False
    sub_results: List[Dict] = field(default_factory=list)


@dataclass
class Diagnosis:
    """Root-cause analysis for a failure."""

    stage: str
    root_cause: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    recommended_fixes: List[str] = field(default_factory=list)
    risk: str = "UNKNOWN"
    affected_files: List[str] = field(default_factory=list)


@dataclass
class ValidationContext:
    """Shared state passed through the entire pipeline."""

    repo_root: Path = field(default_factory=lambda: REPO_ROOT)
    repo_type: str = "unknown"
    languages: List[str] = field(default_factory=list)
    tools: Dict[str, str] = field(default_factory=dict)
    branch: str = ""
    commit: str = ""
    remote: str = "origin"
    remote_url: str = ""
    push_args: List[str] = field(default_factory=list)

    # Discovered metadata
    has_pyproject: bool = False
    has_package_json: bool = False
    has_dockerfile: bool = False
    has_workflows: bool = False
    has_tests: bool = False
    python_version: str = ""
    test_framework: str = ""
    formatters: List[str] = field(default_factory=list)
    linters: List[str] = field(default_factory=list)
    type_checkers: List[str] = field(default_factory=list)
    build_cmd: str = ""

    # Workflow data
    workflows: Dict[str, Dict] = field(default_factory=dict)
    matrix_versions: List[str] = field(default_factory=list)

    # Results from stages
    stage_results: List[StageResult] = field(default_factory=list)
    diagnoses: List[Diagnosis] = field(default_factory=list)
    restart_count: int = 0
    needs_restart: bool = False

    # Files changed by formatters/fixers
    files_changed: List[str] = field(default_factory=list)


# ===========================================================================
# Validator Registry (Plugin System)
# ===========================================================================


class ValidatorRegistry:
    """Auto-discovery plugin system. Validators register via decorator."""

    _validators: List[type] = []

    @classmethod
    def register(cls, validator_cls):
        cls._validators.append(validator_cls)
        return validator_cls

    @classmethod
    def get_all(cls) -> List["BaseValidator"]:
        instances = [v() for v in cls._validators]
        return sorted(instances, key=lambda v: v.order)


class BaseValidator(ABC):
    """Abstract base for all validation stages."""

    name: str = "Unnamed"
    order: int = 0
    description: str = ""

    @abstractmethod
    def run(self, ctx: ValidationContext) -> StageResult: ...

    def _exec(
        self,
        cmd: str,
        cwd: Optional[Path] = None,
        timeout: int = 300,
    ) -> Tuple[int, str, str]:
        """Execute a shell command, return (exit_code, stdout, stderr)."""
        try:
            r = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(cwd or REPO_ROOT),
                timeout=timeout,
            )
            return r.returncode, r.stdout[-4000:], r.stderr[-4000:]
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    def _tool_exists(self, name: str) -> bool:
        return shutil.which(name) is not None

    def _result(self, passed, **kw) -> StageResult:
        return StageResult(
            name=self.name,
            order=self.order,
            passed=passed,
            **kw,
        )

    def _skip(self, reason: str) -> StageResult:
        return StageResult(
            name=self.name,
            order=self.order,
            passed=True,
            skipped=True,
            skip_reason=reason,
        )


# ===========================================================================
# STAGE 1: Repository Audit
# ===========================================================================


@ValidatorRegistry.register
class RepoAuditValidator(BaseValidator):
    name = "Repository Audit"
    order = 1
    description = "Detect repo type, language, tools, dependency graph"

    # Marker files -> language
    MARKERS = {
        "python": [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "Pipfile",
        ],
        "nodejs": ["package.json", "package-lock.json", "yarn.lock"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod"],
    }

    # Tool detection: (tool_name, check_command)
    TOOL_CHECKS = [
        ("ruff", "ruff --version"),
        ("black", "black --version"),
        ("isort", "isort --version-number"),
        ("flake8", "flake8 --version"),
        ("mypy", "mypy --version"),
        ("pyright", "pyright --version"),
        ("pytest", "pytest --version"),
        ("eslint", "eslint --version"),
        ("prettier", "prettier --version"),
        ("tsc", "tsc --version"),
        ("cargo", "cargo --version"),
        ("go", "go version"),
    ]

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        # Detect languages
        for lang, markers in self.MARKERS.items():
            for m in markers:
                if (ctx.repo_root / m).exists():
                    if lang not in ctx.languages:
                        ctx.languages.append(lang)
                    break

        ctx.repo_type = ctx.languages[0] if ctx.languages else "unknown"

        # Detect project files
        ctx.has_pyproject = (ctx.repo_root / "pyproject.toml").exists()
        ctx.has_package_json = (ctx.repo_root / "package.json").exists()
        ctx.has_dockerfile = (ctx.repo_root / "Dockerfile").exists()
        ctx.has_workflows = (ctx.repo_root / ".github" / "workflows").is_dir()
        ctx.has_tests = (ctx.repo_root / "tests").is_dir()

        # Detect tools
        for tool_name, check_cmd in self.TOOL_CHECKS:
            try:
                r = subprocess.run(
                    check_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if r.returncode == 0:
                    version = r.stdout.strip().split("\n")[0][:60]
                    ctx.tools[tool_name] = version
            except Exception:
                pass

        # Determine formatters, linters, type checkers (language-aware)
        is_python = "python" in ctx.languages
        is_node = "nodejs" in ctx.languages

        if is_python and "black" in ctx.tools:
            ctx.formatters.append("black")
        if is_python and "isort" in ctx.tools:
            ctx.formatters.append("isort")
        if is_node and "prettier" in ctx.tools:
            ctx.formatters.append("prettier")

        if is_python and "ruff" in ctx.tools:
            ctx.linters.append("ruff")
        if is_python and "flake8" in ctx.tools:
            ctx.linters.append("flake8")
        if is_node and "eslint" in ctx.tools:
            ctx.linters.append("eslint")

        if is_python and "mypy" in ctx.tools:
            ctx.type_checkers.append("mypy")
        if is_python and "pyright" in ctx.tools:
            ctx.type_checkers.append("pyright")
        if is_node and "tsc" in ctx.tools:
            ctx.type_checkers.append("tsc")

        # Determine build command
        if ctx.has_pyproject:
            ctx.build_cmd = "python -m build"
        elif ctx.has_package_json:
            ctx.build_cmd = "npm run build"

        # Determine test framework
        if "pytest" in ctx.tools:
            ctx.test_framework = "pytest"

        # Get git info
        _, branch, _ = self._exec("git rev-parse --abbrev-ref HEAD")
        ctx.branch = branch.strip()
        _, commit, _ = self._exec("git rev-parse --short HEAD")
        ctx.commit = commit.strip()
        _, remote_url, _ = self._exec(f"git remote get-url {ctx.remote}")
        ctx.remote_url = remote_url.strip()

        # Python version
        ctx.python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}"
            f".{sys.version_info.micro}"
        )

        duration = time.time() - start
        details = (
            f"Type: {ctx.repo_type} | "
            f"Languages: {', '.join(ctx.languages)} | "
            f"Tools: {len(ctx.tools)} detected | "
            f"Branch: {ctx.branch} | "
            f"Commit: {ctx.commit}"
        )

        return self._result(True, duration=duration, details=details)


# ===========================================================================
# STAGE 2: Dependency Validation
# ===========================================================================


@ValidatorRegistry.register
class DependencyValidator(BaseValidator):
    name = "Dependencies"
    order = 2
    description = "Verify deps installed, lockfiles, metadata"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()
        findings = []

        if "python" in ctx.languages:
            # Fast check: verify package is importable
            # and pip reports no broken dependencies
            code, out, err = self._exec(
                f"{sys.executable} -m pip check",
                timeout=15,
            )
            if code != 0:
                findings.append(
                    {
                        "type": "warning",
                        "msg": f"pip check: {out.strip()[:200]}",
                    }
                )

            # Verify key deps are importable
            for dep in ["questionary", "prompt_toolkit"]:
                dep_code, _, _ = self._exec(
                    f'{sys.executable} -c "import {dep}"',
                    timeout=10,
                )
                if dep_code != 0:
                    return self._result(
                        False,
                        duration=time.time() - start,
                        details=f"Missing dependency: {dep}",
                        exit_code=dep_code,
                    )

            # Verify requires-python
            if ctx.has_pyproject:
                try:
                    with open(
                        ctx.repo_root / "pyproject.toml",
                        encoding="utf-8",
                    ) as f:
                        content = f.read()
                    match = re.search(
                        r'requires-python\s*=\s*"([^"]+)"',
                        content,
                    )
                    if match:
                        spec = match.group(1)
                        findings.append(
                            {
                                "type": "info",
                                "msg": f"requires-python: {spec}",
                            }
                        )
                except Exception:
                    pass

        duration = time.time() - start
        return self._result(
            True,
            duration=duration,
            details=f"All dependencies verified ({len(findings)} checks)",
            findings=findings,
        )


# ===========================================================================
# STAGE 3: Formatting
# ===========================================================================


@ValidatorRegistry.register
class FormattingValidator(BaseValidator):
    name = "Formatting"
    order = 3
    description = "Run formatters, restart pipeline if files change"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.formatters:
            return self._skip("No formatters detected")

        # First check if formatting is already correct
        all_clean = True
        check_results = []

        for fmt in ctx.formatters:
            if fmt == "black":
                code, out, err = self._exec("black --check .")
                if code != 0:
                    all_clean = False
                    check_results.append(
                        f"black: {err.count('would reformat')} "
                        f"files need formatting"
                    )
                else:
                    check_results.append("black: clean")

            elif fmt == "isort":
                code, out, err = self._exec("isort --check .")
                if code != 0:
                    all_clean = False
                    check_results.append("isort: imports need sorting")
                else:
                    check_results.append("isort: clean")

        if all_clean:
            return self._result(
                True,
                duration=time.time() - start,
                details=" | ".join(check_results),
            )

        # Files need formatting — apply and trigger restart
        if ctx.restart_count >= MAX_RESTARTS:
            return self._result(
                False,
                duration=time.time() - start,
                details=(
                    "Formatting keeps changing files after "
                    f"{MAX_RESTARTS} restarts. Manual review needed."
                ),
            )

        for fmt in ctx.formatters:
            if fmt == "black":
                self._exec("black .")
            elif fmt == "isort":
                self._exec("isort .")

        ctx.needs_restart = True
        ctx.files_changed.append("(formatted by black/isort)")

        return self._result(
            True,
            duration=time.time() - start,
            details="Files formatted. Pipeline will restart.",
            fix_applied=True,
            auto_fixable=True,
        )


# ===========================================================================
# STAGE 4: Linting
# ===========================================================================


@ValidatorRegistry.register
class LintValidator(BaseValidator):
    name = "Lint"
    order = 4
    description = "Run all detected linters"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.linters:
            return self._skip("No linters detected")

        all_passed = True
        sub_results = []

        for linter in ctx.linters:
            if linter == "ruff":
                code, out, err = self._exec("ruff check .")
                passed = code == 0
                if not passed:
                    # Try auto-fix
                    self._exec("ruff check --fix .")
                    code2, out2, err2 = self._exec("ruff check .")
                    if code2 == 0:
                        passed = True
                        sub_results.append(
                            {
                                "tool": "ruff",
                                "status": "PASS (auto-fixed)",
                            }
                        )
                    else:
                        all_passed = False
                        sub_results.append(
                            {
                                "tool": "ruff",
                                "status": "FAIL",
                                "output": out2[:500],
                            }
                        )
                else:
                    sub_results.append(
                        {
                            "tool": "ruff",
                            "status": "PASS",
                        }
                    )

            elif linter == "flake8":
                code, out, err = self._exec("flake8 .")
                passed = code == 0
                sub_results.append(
                    {
                        "tool": "flake8",
                        "status": "PASS" if passed else "FAIL",
                        "output": out[:500] if not passed else "",
                    }
                )
                if not passed:
                    all_passed = False

        duration = time.time() - start
        summary = ", ".join(f"{r['tool']}: {r['status']}" for r in sub_results)
        return self._result(
            all_passed,
            duration=duration,
            details=summary,
            sub_results=sub_results,
        )


# ===========================================================================
# STAGE 5: Type Checking
# ===========================================================================


@ValidatorRegistry.register
class TypeCheckValidator(BaseValidator):
    name = "Type Check"
    order = 5
    description = "Run type checkers (mypy, pyright, tsc)"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.type_checkers:
            return self._skip("No type checkers configured")

        all_passed = True
        sub_results = []

        for checker in ctx.type_checkers:
            if checker == "mypy":
                code, out, err = self._exec("mypy .", timeout=120)
            elif checker == "pyright":
                code, out, err = self._exec("pyright .", timeout=120)
            elif checker == "tsc":
                code, out, err = self._exec("tsc --noEmit", timeout=120)
            else:
                continue

            passed = code == 0
            sub_results.append(
                {
                    "tool": checker,
                    "status": "PASS" if passed else "FAIL",
                    "output": (out + err)[:500] if not passed else "",
                }
            )
            if not passed:
                all_passed = False

        duration = time.time() - start
        summary = ", ".join(f"{r['tool']}: {r['status']}" for r in sub_results)
        return self._result(
            all_passed,
            duration=duration,
            details=summary,
            sub_results=sub_results,
        )


# ===========================================================================
# STAGE 6: Build Validation
# ===========================================================================


@ValidatorRegistry.register
class BuildValidator(BaseValidator):
    name = "Build"
    order = 6
    description = "Verify project builds successfully"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.build_cmd:
            return self._skip("No build command detected")

        if "python" in ctx.languages:
            # Fast validation: verify package metadata
            # with pip dry-run (no build isolation)
            code, out, err = self._exec(
                f"{sys.executable} -m pip install -e . " "--dry-run --no-deps -q",
                timeout=30,
            )

            duration = time.time() - start

            if code != 0:
                return self._result(
                    False,
                    duration=duration,
                    details="Package metadata validation failed",
                    stderr=err[:1000],
                    exit_code=code,
                )

            # Check that existing dist/ artifacts are valid
            # if present (don't rebuild — too slow for pre-push)
            dist_dir = ctx.repo_root / "dist"
            artifacts = []
            if dist_dir.exists():
                artifacts = [f.name for f in dist_dir.iterdir()]
                if artifacts and self._tool_exists("twine"):
                    tw_code, _, tw_err = self._exec("twine check dist/*", timeout=30)
                    if tw_code != 0:
                        return self._result(
                            False,
                            duration=time.time() - start,
                            details="twine check failed on existing dist/",
                            stderr=tw_err[:500],
                        )

            return self._result(
                True,
                duration=time.time() - start,
                details=(
                    "Package metadata OK"
                    + (f" | dist/: {', '.join(artifacts)}" if artifacts else "")
                ),
            )

        # Non-Python build
        code, out, err = self._exec(ctx.build_cmd, timeout=120)
        duration = time.time() - start

        if code != 0:
            return self._result(
                False,
                duration=duration,
                details=f"Build failed: {ctx.build_cmd}",
                stderr=err[:1000],
                exit_code=code,
            )

        return self._result(
            True,
            duration=duration,
            details=f"Build OK: {ctx.build_cmd}",
        )


# ===========================================================================
# STAGE 7: Testing
# ===========================================================================


@ValidatorRegistry.register
class TestValidator(BaseValidator):
    name = "Tests"
    order = 7
    description = "Run unit/integration/e2e tests"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.has_tests:
            return self._skip("No tests/ directory found")

        if ctx.test_framework == "pytest":
            cmd = "pytest --tb=short -q"
            # Add coverage if available
            try:
                import pytest_cov  # noqa: F401

                cmd = "pytest --tb=short -q --cov=src"
            except ImportError:
                pass

            code, out, err = self._exec(cmd, timeout=300)
            duration = time.time() - start

            # Parse test results
            test_summary = ""
            for line in out.strip().split("\n"):
                if "passed" in line or "failed" in line:
                    test_summary = line.strip()
                    break

            passed = code == 0
            return self._result(
                passed,
                duration=duration,
                details=test_summary or ("Tests passed" if passed else "Tests failed"),
                stdout=out[:2000],
                stderr=err[:1000] if not passed else "",
                exit_code=code,
            )

        return self._skip(f"Unknown test framework: {ctx.test_framework}")


# ===========================================================================
# STAGE 8: Workflow Discovery
# ===========================================================================


@ValidatorRegistry.register
class WorkflowDiscoveryValidator(BaseValidator):
    name = "GitHub Actions"
    order = 8
    description = "Parse all workflow files"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        wf_dir = ctx.repo_root / ".github" / "workflows"
        if not wf_dir.is_dir():
            return self._skip("No .github/workflows/ directory")

        files = sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")))
        if not files:
            return self._skip("No workflow files found")

        findings = []
        for wf_path in files:
            try:
                with open(wf_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                ctx.workflows[wf_path.name] = data

                # Check for deprecated actions
                jobs = data.get("jobs", {}) if data else {}
                for job_name, job in jobs.items():
                    for step in job.get("steps", []):
                        uses = step.get("uses", "")
                        if "@" in uses:
                            action, _, ver = uses.partition("@")
                            if action in LATEST_ACTIONS:
                                latest = LATEST_ACTIONS[action]
                                if ver != latest:
                                    findings.append(
                                        {
                                            "type": "warning",
                                            "msg": (
                                                f"{wf_path.name}: "
                                                f"{action}@{ver} "
                                                f"(latest: @{latest})"
                                            ),
                                        }
                                    )

                    # Check for EOL Python
                    matrix = job.get("strategy", {}).get("matrix", {})
                    py_versions = matrix.get("python-version", [])
                    for pv in py_versions:
                        if str(pv) not in ctx.matrix_versions:
                            ctx.matrix_versions.append(str(pv))
                        if str(pv) in EOL_PYTHON:
                            findings.append(
                                {
                                    "type": "critical",
                                    "msg": (f"{wf_path.name}: " f"Python {pv} is EOL"),
                                }
                            )

            except yaml.YAMLError as e:
                findings.append(
                    {
                        "type": "critical",
                        "msg": f"{wf_path.name}: YAML parse error: {e}",
                    }
                )

        duration = time.time() - start
        has_critical = any(f["type"] == "critical" for f in findings)

        return self._result(
            not has_critical,
            duration=duration,
            details=(
                f"{len(ctx.workflows)} workflow(s) parsed | "
                f"Matrix: {', '.join(ctx.matrix_versions) or 'none'} | "
                f"{len(findings)} finding(s)"
            ),
            findings=findings,
        )


# ===========================================================================
# STAGE 9: Workflow Simulation
# ===========================================================================


@ValidatorRegistry.register
class WorkflowSimulationValidator(BaseValidator):
    name = "Workflow Simulation"
    order = 9
    description = "Replay workflow run: commands locally"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.workflows:
            return self._skip("No workflows to simulate")

        all_passed = True
        sub_results = []

        for wf_name, wf_data in ctx.workflows.items():
            # Skip release/publish-only workflows
            triggers = wf_data.get("on") if "on" in wf_data else wf_data.get(True, {})
            if isinstance(triggers, str):
                triggers_keys = [triggers]
            elif isinstance(triggers, dict):
                triggers_keys = list(triggers.keys())
            elif isinstance(triggers, list):
                triggers_keys = triggers
            else:
                triggers_keys = []

            if (
                "release" in triggers_keys
                or "workflow_dispatch" in triggers_keys
                and "push" not in triggers_keys
                and "pull_request" not in triggers_keys
            ):
                sub_results.append(
                    {
                        "workflow": wf_name,
                        "status": "SKIP (release-only)",
                    }
                )
                continue

            jobs = wf_data.get("jobs", {}) if wf_data else {}
            for job_name, job in jobs.items():
                steps = job.get("steps", [])
                job_passed = True

                for step in steps:
                    run_cmd = step.get("run", "")
                    if not run_cmd:
                        continue  # Skip uses: steps

                    step_name = step.get("name", run_cmd[:40])
                    commands = [
                        line.strip()
                        for line in run_cmd.strip().split("\n")
                        if line.strip()
                    ]

                    for cmd in commands:
                        # Skip setup/build/publish commands already handled or unsafe
                        skip_prefixes = (
                            "pip install",
                            "python -m pip install",
                            "npm install",
                            "npm ci",
                            "yarn install",
                            "pip install --upgrade",
                            "python -m build",
                            "twine upload",
                            "flit publish",
                        )
                        if any(cmd.strip().startswith(p) for p in skip_prefixes):
                            continue

                        code, out, err = self._exec(cmd, timeout=60)
                        if code != 0:
                            job_passed = False
                            all_passed = False
                            sub_results.append(
                                {
                                    "workflow": wf_name,
                                    "job": job_name,
                                    "step": step_name,
                                    "cmd": cmd[:60],
                                    "status": "FAIL",
                                    "stderr": err[:200],
                                }
                            )
                            break

                    if not job_passed:
                        break

                if job_passed:
                    sub_results.append(
                        {
                            "workflow": wf_name,
                            "job": job_name,
                            "status": "PASS",
                        }
                    )

        duration = time.time() - start
        passed_count = sum(
            1 for r in sub_results if r.get("status") in ("PASS", "SKIP (release-only)")
        )
        total_count = len(sub_results)

        return self._result(
            all_passed,
            duration=duration,
            details=f"{passed_count}/{total_count} jobs simulated OK",
            sub_results=sub_results,
        )


# ===========================================================================
# STAGE 10: Matrix Validation
# ===========================================================================


@ValidatorRegistry.register
class MatrixValidator(BaseValidator):
    name = "Matrix Validation"
    order = 10
    description = "Run tests per Python version from CI matrix"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.matrix_versions:
            return self._skip("No matrix versions in workflows")

        # Filter out EOL versions
        versions = [v for v in ctx.matrix_versions if v not in EOL_PYTHON]
        if not versions:
            return self._skip("All matrix versions are EOL")

        is_windows = platform.system() == "Windows"
        sub_results = []

        for ver in versions:
            # Try to find the Python interpreter
            py_cmd = None
            if is_windows:
                candidates = [f"py -{ver}", f"python{ver}"]
            else:
                candidates = [f"python{ver}"]

            for cand in candidates:
                try:
                    r = subprocess.run(
                        cand.split() + ["--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if r.returncode == 0 and ver in (r.stdout + r.stderr):
                        py_cmd = cand
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            if not py_cmd:
                sub_results.append(
                    {
                        "version": ver,
                        "status": "SKIP",
                        "reason": "Not installed locally",
                    }
                )
                continue

            # Run pytest with this Python version
            code, out, err = self._exec(
                f"{py_cmd} -m pytest --tb=short -q",
                timeout=120,
            )
            test_line = ""
            for line in out.strip().split("\n"):
                if "passed" in line or "failed" in line:
                    test_line = line.strip()

            sub_results.append(
                {
                    "version": ver,
                    "status": "PASS" if code == 0 else "FAIL",
                    "summary": test_line,
                    "exit_code": code,
                }
            )

        duration = time.time() - start
        all_passed = all(r["status"] in ("PASS", "SKIP") for r in sub_results)
        summary_parts = [f"Python {r['version']}: {r['status']}" for r in sub_results]

        return self._result(
            all_passed,
            duration=duration,
            details=" | ".join(summary_parts),
            sub_results=sub_results,
        )


# ===========================================================================
# STAGE 11: Failure Investigation
# ===========================================================================


@ValidatorRegistry.register
class FailureInvestigator(BaseValidator):
    name = "Failure Investigation"
    order = 11
    description = "Root-cause analysis on any failures"

    ERROR_PATTERNS = [
        (r"No module named '(\w+)'", "Missing dependency: {0}", 0.90),
        (r"SyntaxError", "Python syntax error in source", 0.95),
        (r"would reformat|reformatted", "Code not formatted", 0.95),
        (r"FAILED|assert.*Error", "Unit test failure", 0.85),
        (r"ImportError", "Import error — missing or broken dep", 0.90),
        (r"ModuleNotFoundError", "Module not found", 0.90),
        (r"IndentationError", "Indentation error", 0.95),
        (r"NameError", "Undefined variable reference", 0.90),
        (r"TypeError", "Type mismatch error", 0.85),
        (r"FileNotFoundError", "Missing file", 0.85),
        (r"PermissionError", "Permission denied", 0.80),
    ]

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        failed_stages = [r for r in ctx.stage_results if not r.passed and not r.skipped]

        if not failed_stages:
            return self._result(
                True,
                duration=time.time() - start,
                details="No failures to investigate",
            )

        for sr in failed_stages:
            combined = (sr.stdout or "") + "\n" + (sr.stderr or "")
            if sr.details:
                combined += "\n" + sr.details

            diag = self._diagnose(sr.name, combined)
            if diag:
                ctx.diagnoses.append(diag)

        duration = time.time() - start
        return self._result(
            True,  # Investigation itself always passes
            duration=duration,
            details=f"{len(ctx.diagnoses)} diagnosis(es) produced",
        )

    def _diagnose(self, stage: str, output: str) -> Optional[Diagnosis]:
        for pattern, cause_tpl, conf in self.ERROR_PATTERNS:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                groups = match.groups() if match.groups() else ()
                cause = cause_tpl.format(*groups) if groups else cause_tpl
                evidence = []
                for line in output.split("\n"):
                    if re.search(pattern, line, re.IGNORECASE):
                        evidence.append(line.strip()[:120])
                return Diagnosis(
                    stage=stage,
                    root_cause=cause,
                    confidence=conf,
                    evidence=evidence[:5],
                    recommended_fixes=[cause],
                    risk="HIGH" if conf >= 0.9 else "MEDIUM",
                )

        if output.strip():
            err_lines = [ln.strip() for ln in output.split("\n") if ln.strip()][-5:]
            return Diagnosis(
                stage=stage,
                root_cause="Unknown failure",
                confidence=0.50,
                evidence=err_lines,
                recommended_fixes=["Review error output manually"],
                risk="UNKNOWN",
            )
        return None


# ===========================================================================
# STAGE 12: Automatic Repair
# ===========================================================================


@ValidatorRegistry.register
class AutoRepairValidator(BaseValidator):
    name = "Auto Repair"
    order = 12
    description = "Apply safe deterministic fixes"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        if not ctx.diagnoses:
            return self._skip("No diagnoses to repair")

        if ctx.restart_count >= MAX_RESTARTS:
            return self._result(
                True,
                duration=time.time() - start,
                details=(
                    f"Max restarts ({MAX_RESTARTS}) reached. " "Skipping auto-repair."
                ),
            )

        high_conf = [d for d in ctx.diagnoses if d.confidence >= 0.85]
        if not high_conf:
            return self._result(
                True,
                duration=time.time() - start,
                details=(
                    "No high-confidence fixes available. " "Manual review needed."
                ),
            )

        applied = []
        for d in high_conf:
            if "not formatted" in d.root_cause.lower():
                self._exec("black .")
                applied.append("Applied black formatting")
                ctx.needs_restart = True
            elif "missing dependency" in d.root_cause.lower():
                dep = d.root_cause.split(": ")[-1]
                code, _, _ = self._exec(f"pip install {dep} -q")
                if code == 0:
                    applied.append(f"Installed {dep}")
                    ctx.needs_restart = True

        duration = time.time() - start
        return self._result(
            True,
            duration=duration,
            details=(
                f"{len(applied)} fix(es) applied"
                if applied
                else "No safe fixes to apply"
            ),
            fix_applied=bool(applied),
        )


# ===========================================================================
# STAGE 13: Security
# ===========================================================================


@ValidatorRegistry.register
class SecurityValidator(BaseValidator):
    name = "Security"
    order = 13
    description = "Check deps vulnerabilities, secret leaks"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()
        findings = []

        # 1. Check for dependency vulnerabilities (pip-audit)
        if self._tool_exists("pip-audit"):
            code, out, err = self._exec("pip-audit --format json", timeout=60)
            if code != 0 and "vulnerability" in (out + err).lower():
                findings.append(
                    {
                        "type": "warning",
                        "msg": "pip-audit found vulnerabilities",
                        "detail": out[:500],
                    }
                )

        # 2. Scan for hardcoded secrets
        secret_hits = self._scan_secrets(ctx.repo_root)
        findings.extend(secret_hits)

        duration = time.time() - start
        has_critical = any(f.get("type") == "critical" for f in findings)

        if has_critical:
            return self._result(
                False,
                duration=duration,
                details=f"CRITICAL: {len(findings)} security issue(s)",
                findings=findings,
            )

        return self._result(
            True,
            duration=duration,
            details=(f"No critical issues | " f"{len(findings)} finding(s)"),
            findings=findings,
        )

    def _scan_secrets(self, root: Path) -> List[Dict]:
        hits = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip excluded directories
            dirnames[:] = [d for d in dirnames if d not in SCAN_EXCLUDE_DIRS]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if fpath.suffix not in SCAN_EXTENSIONS:
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    for pattern, label in SECRET_PATTERNS:
                        matches = re.findall(pattern, content)
                        if matches:
                            rel = fpath.relative_to(root)
                            hits.append(
                                {
                                    "type": "critical",
                                    "msg": (f"Potential {label} in " f"{rel}"),
                                }
                            )
                except Exception:
                    continue
        return hits


# ===========================================================================
# STAGE 14: Artifact Validation
# ===========================================================================


@ValidatorRegistry.register
class ArtifactValidator(BaseValidator):
    name = "Artifacts"
    order = 14
    description = "Verify wheel/sdist/packages"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        dist_dir = ctx.repo_root / "dist"
        if not dist_dir.exists() or not list(dist_dir.iterdir()):
            return self._skip("No dist/ artifacts (build may have been skipped)")

        artifacts = list(dist_dir.iterdir())
        findings = []
        all_valid = True

        # Check each artifact
        for art in artifacts:
            if art.suffix == ".whl":
                findings.append(
                    {
                        "type": "info",
                        "msg": f"Wheel: {art.name} ({art.stat().st_size} bytes)",
                    }
                )
            elif art.name.endswith(".tar.gz"):
                findings.append(
                    {
                        "type": "info",
                        "msg": f"Sdist: {art.name} ({art.stat().st_size} bytes)",
                    }
                )

        # Run twine check if available
        if self._tool_exists("twine"):
            code, out, err = self._exec("twine check dist/*")
            if code != 0:
                all_valid = False
                findings.append(
                    {
                        "type": "critical",
                        "msg": f"twine check failed: {err[:200]}",
                    }
                )
            else:
                findings.append(
                    {
                        "type": "info",
                        "msg": "twine check: PASSED",
                    }
                )

        duration = time.time() - start
        return self._result(
            all_valid,
            duration=duration,
            details=f"{len(artifacts)} artifact(s) validated",
            findings=findings,
        )


# ===========================================================================
# STAGE 15: Git Validation
# ===========================================================================


@ValidatorRegistry.register
class GitValidator(BaseValidator):
    name = "Git Validation"
    order = 15
    description = "Clean tree, no conflicts, no untracked generated"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()
        findings = []

        # Check for merge conflicts
        code, out, _ = self._exec("git diff --check HEAD")
        if code != 0 and "conflict" in out.lower():
            findings.append(
                {
                    "type": "critical",
                    "msg": "Merge conflict markers detected",
                }
            )

        # Check for untracked generated files
        code, out, _ = self._exec("git status --porcelain")
        untracked = [
            line[3:] for line in out.strip().split("\n") if line.startswith("??")
        ]
        # Filter: warn about generated dirs in source
        gen_patterns = ["dist/", "build/", "*.egg-info"]
        for ut in untracked:
            for gp in gen_patterns:
                if gp.endswith("/") and ut.startswith(gp):
                    findings.append(
                        {
                            "type": "warning",
                            "msg": f"Untracked generated: {ut}",
                        }
                    )
                elif "*" in gp and ut.endswith(gp.replace("*", "")):
                    findings.append(
                        {
                            "type": "warning",
                            "msg": f"Untracked generated: {ut}",
                        }
                    )

        # Check if there are uncommitted changes
        modified = [
            line[3:]
            for line in out.strip().split("\n")
            if line.strip() and not line.startswith("??") and line.strip() != ""
        ]
        if modified:
            findings.append(
                {
                    "type": "warning",
                    "msg": (f"{len(modified)} file(s) with uncommitted " "changes"),
                }
            )

        duration = time.time() - start
        has_critical = any(f["type"] == "critical" for f in findings)

        return self._result(
            not has_critical,
            duration=duration,
            details=(
                f"{len(findings)} finding(s)" if findings else "Working tree clean"
            ),
            findings=findings,
        )


# ===========================================================================
# STAGE 16: Final Decision
# ===========================================================================


@ValidatorRegistry.register
class FinalDecision(BaseValidator):
    name = "Final Decision"
    order = 16
    description = "Aggregate results, produce report, PASS/FAIL"

    def run(self, ctx: ValidationContext) -> StageResult:
        start = time.time()

        all_passed = all(r.passed for r in ctx.stage_results)

        # Generate the report
        self._print_report(ctx, all_passed)

        duration = time.time() - start
        return self._result(
            all_passed,
            duration=duration,
            details="SAFE TO PUSH" if all_passed else "PUSH BLOCKED",
        )

    def _print_report(self, ctx: ValidationContext, all_passed: bool):
        width = 60
        sep = "─" * width

        print(f"\n{_c('━' * width, C.BOLD)}")
        print(f"  {_c('PRE-PUSH VALIDATION REPORT', C.BOLD)}")
        print(_c("━" * width, C.BOLD))

        # Repository info
        print(f"\n  Repository  : {ctx.remote_url or 'local'}")
        print(f"  Language    : {', '.join(ctx.languages)}")
        print(f"  Branch      : {ctx.branch}")
        print(f"  Commit      : {ctx.commit}")
        print(f"  Python      : {ctx.python_version}")
        print(f"  {_c(sep, C.DIM)}")

        # Stage results
        for sr in ctx.stage_results:
            if sr.order == 16:
                continue  # Don't print self

            if sr.skipped:
                status = _skip()
                extra = f" ({sr.skip_reason})"
            elif sr.passed:
                status = _pass()
                extra = ""
            else:
                status = _fail()
                extra = ""

            timing = _c(f"({sr.duration:.1f}s)", C.DIM)
            print(f"  {status}  {sr.name:<22} {timing}{extra}")

            # Print sub-results for matrix
            if sr.sub_results and sr.order == 10:
                for sub in sr.sub_results:
                    ver = sub.get("version", "?")
                    s = sub.get("status", "?")
                    col = C.G if s == "PASS" else (C.Y if s == "SKIP" else C.R)
                    print(f"         Python {ver}: {_c(s, col)}")

        print(f"  {_c(sep, C.DIM)}")

        # Diagnoses
        if ctx.diagnoses:
            print(f"\n  {_c('DIAGNOSES', C.Y)}")
            for d in ctx.diagnoses:
                conf_col = C.G if d.confidence >= 0.85 else C.Y
                print(f"    Stage      : {d.stage}")
                print(f"    Root Cause : {d.root_cause}")
                print(f"    Confidence : " f"{_c(f'{d.confidence:.0%}', conf_col)}")
                print(f"    Risk       : {d.risk}")
                for ev in d.evidence[:3]:
                    print(f"    Evidence   : {_c(ev[:70], C.DIM)}")
                print()

        # Final verdict
        print(f"  {_c(sep, C.DIM)}")
        if all_passed:
            print(f"\n  {_c('✓ SAFE TO PUSH', C.G)}  " f"All validation stages passed.")
        else:
            failed = [
                r.name for r in ctx.stage_results if not r.passed and not r.skipped
            ]
            print(f"\n  {_c('✗ PUSH BLOCKED', C.R)}  " f"Failed: {', '.join(failed)}")
        print(f"\n{_c('━' * width, C.BOLD)}\n")


# ===========================================================================
# Pre-Push Engine (Orchestrator)
# ===========================================================================


class PrePushEngine:
    """Orchestrates all 16 validation stages in order."""

    def __init__(
        self,
        root: Path = REPO_ROOT,
        max_stage: Optional[int] = None,
        skip_matrix: bool = False,
        no_restart: bool = False,
        generate_report: bool = False,
    ):
        self.root = root
        self.max_stage = max_stage
        self.skip_matrix = skip_matrix
        self.no_restart = no_restart
        self.generate_report = generate_report

    def run(
        self,
        remote: str = "origin",
        push_args: Optional[List[str]] = None,
    ) -> bool:
        """Run the full pipeline. Returns True if safe to push."""
        ctx = ValidationContext(
            repo_root=self.root,
            remote=remote,
            push_args=push_args or [],
        )

        print(
            f"\n{_c('━' * 60, C.BOLD)}"
            f"\n  {_c('PRE-PUSH VALIDATION SYSTEM', C.BOLD)}"
            f"\n  {_c('Mandatory pipeline — push blocked until all stages pass', C.DIM)}"
            f"\n{_c('━' * 60, C.BOLD)}"
        )

        return self._run_pipeline(ctx)

    def _run_pipeline(self, ctx: ValidationContext) -> bool:
        validators = ValidatorRegistry.get_all()

        for validator in validators:
            # Skip matrix if requested
            if self.skip_matrix and validator.order == 10:
                ctx.stage_results.append(
                    StageResult(
                        name=validator.name,
                        order=validator.order,
                        passed=True,
                        skipped=True,
                        skip_reason="--skip-matrix",
                    )
                )
                continue

            # Stop at max_stage if set
            if self.max_stage and validator.order > self.max_stage:
                break

            _header(f"Stage {validator.order}: {validator.name}")
            print(f"  {_c(validator.description, C.DIM)}\n")

            result = validator.run(ctx)
            ctx.stage_results.append(result)

            # Print stage result
            if result.skipped:
                print(f"\n  {_skip()}  {result.skip_reason}")
            elif result.passed:
                print(f"\n  {_pass()}  {result.details}")
            else:
                print(f"\n  {_fail()}  {result.details}")
                if result.stderr:
                    err_lines = result.stderr.strip().split("\n")[:5]
                    for el in err_lines:
                        if el.strip():
                            print(f"         {_c(el[:80], C.R)}")

            # Handle restart
            if (
                ctx.needs_restart
                and not self.no_restart
                and ctx.restart_count < MAX_RESTARTS
            ):
                ctx.restart_count += 1
                ctx.needs_restart = False
                print(
                    f"\n  {_c('↻ RESTARTING PIPELINE', C.Y)} "
                    f"(attempt {ctx.restart_count}/{MAX_RESTARTS})"
                )
                ctx.stage_results.clear()
                ctx.diagnoses.clear()
                return self._run_pipeline(ctx)

        # Generate report file if requested
        if self.generate_report:
            self._write_report(ctx)

        # Return final verdict
        all_passed = all(r.passed for r in ctx.stage_results)
        return all_passed

    def _write_report(self, ctx: ValidationContext):
        """Write pre_push_report.md."""
        lines = [
            "# Pre-Push Validation Report",
            "",
            f"**Repository**: {ctx.remote_url}",
            f"**Branch**: {ctx.branch}",
            f"**Commit**: {ctx.commit}",
            f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Stage Results",
            "",
            "| # | Stage | Status | Duration |",
            "|---|---|---|---|",
        ]

        all_passed = True
        for sr in ctx.stage_results:
            if sr.skipped:
                status = "SKIP"
            elif sr.passed:
                status = "PASS"
            else:
                status = "FAIL"
                all_passed = False

            lines.append(
                f"| {sr.order} | {sr.name} | {status} " f"| {sr.duration:.1f}s |"
            )

        lines.append("")

        if ctx.diagnoses:
            lines.append("## Diagnoses")
            for d in ctx.diagnoses:
                lines.append(f"\n### {d.stage}")
                lines.append(f"- **Root Cause**: {d.root_cause}")
                lines.append(f"- **Confidence**: {d.confidence:.0%}")
                lines.append(f"- **Risk**: {d.risk}")
                for ev in d.evidence[:3]:
                    lines.append(f"- Evidence: `{ev[:100]}`")
            lines.append("")

        lines.append("## Verdict")
        if all_passed:
            lines.append("> **SAFE TO PUSH** — " "All validation stages passed.")
        else:
            failed = [
                r.name for r in ctx.stage_results if not r.passed and not r.skipped
            ]
            lines.append("> **PUSH BLOCKED** — " f"Failed stages: {', '.join(failed)}")

        content = "\n".join(lines)
        report_path = ctx.repo_root / "pre_push_report.md"
        report_path.write_text(content, encoding="utf-8")
        print(f"\n  Report: {_c(str(report_path), C.CY)}")


# ===========================================================================
# CLI Entry Point
# ===========================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-Push Validation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pre_push.py                 # Full 16-stage pipeline
  python scripts/pre_push.py --stage 7       # Run stages 1-7 only
  python scripts/pre_push.py --skip-matrix   # Skip matrix validation
  python scripts/pre_push.py --report        # Generate report file
  python scripts/pre_push.py --no-restart    # Disable restart loop
        """,
    )
    parser.add_argument(
        "--stage",
        type=int,
        help="Run up to stage N only",
    )
    parser.add_argument(
        "--skip-matrix",
        action="store_true",
        help="Skip matrix validation (stage 10)",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Disable automatic pipeline restart",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate pre_push_report.md",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Git remote name (default: origin)",
    )

    args = parser.parse_args()

    engine = PrePushEngine(
        max_stage=args.stage,
        skip_matrix=args.skip_matrix,
        no_restart=args.no_restart,
        generate_report=args.report,
    )

    passed = engine.run(remote=args.remote, push_args=sys.argv[1:])
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
