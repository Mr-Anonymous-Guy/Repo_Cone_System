import os
import socket
import subprocess
import sys
from dataclasses import dataclass
from typing import List

from repo_clone_system import __version__
from repo_clone_system.core.utils import check_git
from repo_clone_system.storage.memory import get_config_dir, get_memory_file


@dataclass
class CheckResult:
    label: str
    status: str  # "✔", "✖", "⚠"
    passed: bool
    details: str
    suggestion: str = ""


def _check_internet() -> bool:
    """Quick socket check to verify internet connectivity."""
    try:
        socket.setdefaulttimeout(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("1.1.1.1", 53))
        s.close()
        return True
    except Exception:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("8.8.8.8", 53))
            s.close()
            return True
        except Exception:
            return False


def _check_github() -> bool:
    """Quick socket check to verify GitHub connectivity."""
    try:
        socket.setdefaulttimeout(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("github.com", 443))
        s.close()
        return True
    except Exception:
        return False


def run_doctor() -> List[CheckResult]:
    """Runs system diagnostics for 'repo doctor'."""
    results = []

    # 1. Git Installed
    has_git = check_git()
    if has_git:
        try:
            v = (
                subprocess.check_output(["git", "--version"], text=True)
                .strip()
                .split("\n")[0]
            )
        except Exception:
            v = "Git detected"
        results.append(
            CheckResult(
                label="Git Installed",
                status="✔",
                passed=True,
                details=v,
            )
        )
    else:
        results.append(
            CheckResult(
                label="Git Installed",
                status="✖",
                passed=False,
                details="Git not found in PATH",
                suggestion="Install Git from https://git-scm.com/",
            )
        )

    # 2. Python Version
    py_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    py_ok = sys.version_info >= (3, 9)
    results.append(
        CheckResult(
            label="Python Version",
            status="✔" if py_ok else "⚠",
            passed=py_ok,
            details=f"Python {py_ver} ({sys.executable})",
            suggestion=(
                ""
                if py_ok
                else "Upgrade Python to 3.9 or higher for optimal compatibility"
            ),
        )
    )

    # 3. Internet Connectivity
    net_ok = _check_internet()
    results.append(
        CheckResult(
            label="Internet Connectivity",
            status="✔" if net_ok else "⚠",
            passed=net_ok,
            details=(
                "Connected to external network"
                if net_ok
                else "Offline / network check failed"
            ),
            suggestion=(
                ""
                if net_ok
                else "Check network cables, Wi-Fi connection, or firewall settings"
            ),
        )
    )

    # 4. GitHub Connectivity
    gh_ok = _check_github()
    results.append(
        CheckResult(
            label="GitHub Connectivity",
            status="✔" if gh_ok else "⚠",
            passed=gh_ok,
            details=(
                "github.com accessible (port 443)"
                if gh_ok
                else "Cannot reach github.com"
            ),
            suggestion=(
                ""
                if gh_ok
                else "Check internet connection or proxy settings to reach github.com"
            ),
        )
    )

    # 5. Configuration Folder
    config_dir = get_config_dir()
    cfg_exists = config_dir.exists()
    cfg_writable = os.access(str(config_dir.parent), os.W_OK)
    if cfg_exists and os.access(str(config_dir), os.W_OK):
        results.append(
            CheckResult(
                label="Configuration Folder",
                status="✔",
                passed=True,
                details=f"Writable directory: {config_dir}",
            )
        )
    elif cfg_writable:
        results.append(
            CheckResult(
                label="Configuration Folder",
                status="✔",
                passed=True,
                details=f"Parent writable: {config_dir}",
            )
        )
    else:
        results.append(
            CheckResult(
                label="Configuration Folder",
                status="✖",
                passed=False,
                details=f"Permission denied: {config_dir}",
                suggestion="Grant write permissions for the configuration folder",
            )
        )

    # 6. Memory File
    memory_file = get_memory_file()
    mem_ok = memory_file.exists() and os.access(str(memory_file), os.R_OK)
    results.append(
        CheckResult(
            label="Memory File",
            status="✔" if mem_ok else "⚠",
            passed=mem_ok,
            details=(
                f"Memory file accessible at {memory_file}"
                if mem_ok
                else f"Memory file will be created on first write at {memory_file}"
            ),
            suggestion="",
        )
    )

    # 7. Package Version
    results.append(
        CheckResult(
            label="Package Version",
            status="✔",
            passed=True,
            details=f"repo-clone-system v{__version__}",
        )
    )

    return results
