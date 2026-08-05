#!/usr/bin/env python3
"""
Install / uninstall the Pre-Push Validation git hook.

Usage:
    python scripts/install_hooks.py              # Install hook
    python scripts/install_hooks.py --uninstall  # Remove hook
    python scripts/install_hooks.py --status     # Check if installed
"""

import argparse
import stat
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_SRC = REPO_ROOT / ".githooks"
GIT_HOOKS_DIR = REPO_ROOT / ".git" / "hooks"

HOOK_SCRIPT_UNIX = """\
#!/bin/sh
# Pre-Push Validation System — installed by install_hooks.py
# This hook runs the full validation pipeline before every push.
# To bypass (emergency only): git push --no-verify

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Pre-Push Validation System activated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python "$SCRIPT_DIR/scripts/pre_push.py" --report "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ PUSH BLOCKED — Validation failed."
    echo "  Fix the issues above and try again."
    echo "  Emergency bypass: git push --no-verify"
    echo ""
    exit 1
fi

exit 0
"""

HOOK_SCRIPT_WINDOWS = """\
@echo off
REM Pre-Push Validation System — installed by install_hooks.py
REM This hook runs the full validation pipeline before every push.
REM To bypass (emergency only): git push --no-verify

set SCRIPT_DIR=%~dp0..\\..

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   Pre-Push Validation System activated
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python "%SCRIPT_DIR%\\scripts\\pre_push.py" --report %*
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% NEQ 0 (
    echo.
    echo [91m✗ PUSH BLOCKED — Validation failed.[0m
    echo   Fix the issues above and try again.
    echo   Emergency bypass: git push --no-verify
    echo.
    exit /b 1
)

exit /b 0
"""


def install():
    """Install the pre-push hook."""
    GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    hook_path = GIT_HOOKS_DIR / "pre-push"

    # Backup existing hook
    if hook_path.exists():
        backup = hook_path.with_suffix(".backup")
        hook_path.replace(backup)
        print(f"  Backed up existing hook to: {backup.name}")

    # Write hook (use Unix script — Git for Windows uses sh)
    hook_path.write_text(HOOK_SCRIPT_UNIX, encoding="utf-8")

    # Make executable (Unix/macOS)
    try:
        hook_path.chmod(
            hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
        )
    except Exception:
        pass  # Windows doesn't need chmod

    # Also create .githooks/ for version control
    HOOKS_SRC.mkdir(parents=True, exist_ok=True)
    src_hook = HOOKS_SRC / "pre-push"
    src_hook.write_text(HOOK_SCRIPT_UNIX, encoding="utf-8")

    print()
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  ✓ Pre-Push Validation hook installed!")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(f"  Hook: {hook_path}")
    print()
    print("  Every 'git push' will now run the validation")
    print("  pipeline before allowing the push to proceed.")
    print()
    print("  Emergency bypass: git push --no-verify")
    print()


def uninstall():
    """Remove the pre-push hook."""
    hook_path = GIT_HOOKS_DIR / "pre-push"

    if not hook_path.exists():
        print("  No pre-push hook found. Nothing to remove.")
        return

    hook_path.unlink()
    print()
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  ✓ Pre-Push Validation hook removed.")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Restore backup if exists
    backup = hook_path.with_suffix(".backup")
    if backup.exists():
        backup.rename(hook_path)
        print("  Previous hook restored from backup.")
    print()


def status():
    """Check if the hook is installed."""
    hook_path = GIT_HOOKS_DIR / "pre-push"

    if hook_path.exists():
        content = hook_path.read_text(encoding="utf-8", errors="ignore")
        is_ours = "Pre-Push Validation System" in content
        if is_ours:
            print("  ✓ Pre-Push Validation hook is INSTALLED")
        else:
            print("  ⚠ A pre-push hook exists but is NOT ours")
    else:
        print("  ✗ Pre-Push Validation hook is NOT installed")
        print("  Run: python scripts/install_hooks.py")


def main():
    parser = argparse.ArgumentParser(
        description="Install/uninstall the Pre-Push Validation git hook",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the pre-push hook",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check if the hook is installed",
    )

    args = parser.parse_args()

    if args.uninstall:
        uninstall()
    elif args.status:
        status()
    else:
        install()


if __name__ == "__main__":
    main()
