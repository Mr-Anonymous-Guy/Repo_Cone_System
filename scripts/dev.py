"""Developer helper script for running tests and formatting checks."""

import subprocess
import sys


def run_command(cmd, description):
    print("=" * 50)
    print(f" Running: {description}")
    print(f" Command: {' '.join(cmd)}")
    print("=" * 50)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n[FAILED] {description} failed!\n")
        sys.exit(result.returncode)
    print(f"\n[OK] {description} passed!\n")


def main():
    # Run Pytest
    run_command([sys.executable, "-m", "pytest"], "Pytest Test Suite")


if __name__ == "__main__":
    main()
