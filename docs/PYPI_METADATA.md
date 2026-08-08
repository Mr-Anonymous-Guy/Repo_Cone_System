# PyPI Package Metadata & Distribution Specification

This document details the packaging metadata, project identity, and release architecture for `repo-clone-system`.

## Package Identity & Overview

| Attribute | Value |
|---|---|
| **Distribution Name** | `repo-clone-system` |
| **Import Package** | `repo_clone_system` |
| **CLI Executable** | `repo` |
| **Current Package Version** | `0.3.1` |
| **Build Backend** | `setuptools.build_meta` (PEP 517 / PEP 621) |
| **License** | `MIT` (`LICENSE` file included) |
| **Author** | `Mr. Anonymous` (`mr.anonymous071105@gmail.com`) |
| **Python Version Requirement** | `>=3.9` |

## Packaging Architecture (`pyproject.toml`)

`pyproject.toml` serves as the authoritative, single source of truth for all packaging metadata following [PEP 621](https://peps.python.org/pep-0621/).

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "repo-clone-system"
version = "0.3.1"
description = "A developer-focused CLI for cloning, configuring, validating, and managing Git repositories."
readme = { file = "README.md", content-type = "text/markdown" }
requires-python = ">=3.9"
license = { text = "MIT" }
license-files = ["LICENSE"]
keywords = [
    "cli",
    "git",
    "github",
    "repository",
    "clone",
    "workspace",
    "developer-tools",
    "automation",
    "terminal"
]
authors = [
    { name = "Mr. Anonymous", email = "mr.anonymous071105@gmail.com" }
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Build Tools",
    "Topic :: Software Development :: Version Control",
    "Topic :: Utilities"
]
dependencies = [
    "questionary>=2.0.0",
    "prompt-toolkit>=3.0.0"
]

[project.urls]
Homepage = "https://github.com/Mr-Anonymous-Guy/Repo_Cone_System"
Repository = "https://github.com/Mr-Anonymous-Guy/Repo_Cone_System"
Issues = "https://github.com/Mr-Anonymous-Guy/Repo_Cone_System/issues"
Documentation = "https://github.com/Mr-Anonymous-Guy/Repo_Cone_System#readme"
Changelog = "https://github.com/Mr-Anonymous-Guy/Repo_Cone_System/blob/main/CHANGELOG.md"

[project.scripts]
repo = "repo_clone_system.cli:cli_entry_point"
```

## Long Description & PyPI Rendering Compatibility

- **Source File**: `README.md` configured via `readme = { file = "README.md", content-type = "text/markdown" }`.
- **Link Resolution**: All internal relative links (such as `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`) are formatted as absolute GitHub repository links so that when rendered on the PyPI package page, all hyperlinks function without breakage.
- **Badges**: PyPI version, Python versions, MIT license, CI build status, and download badges are embedded at the top of the README.

## Packaging Build & Validation Pipeline

### 1. Artifact Cleaning & Generation
Before generating distribution artifacts, remove previous build directories:
```bash
python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('dist'), pathlib.Path('src/repo_clone_system.egg-info')]]"
python -m build
```

### 2. Package Metadata Validation
Validate wheel and sdist core metadata against PyPI standards:
```bash
python -m twine check dist/*
```

### 3. Wheel & SDist Inspection
Verify that `.whl` and `.tar.gz` contain required source modules (`src/repo_clone_system/`), storage resources (`storage/*.json`), entry point scripts, `LICENSE`, `pyproject.toml`, and `README.md`, while excluding development caches, credentials, logs, `.git`, or temporary files.

### 4. Clean Virtual Environment Smoke Test
Install the built wheel into a fresh virtual environment to verify standalone CLI execution:
```bash
python -m venv .release-test-env
.release-test-env\Scripts\python.exe -m pip install dist/repo_clone_system-0.3.1-py3-none-any.whl
.release-test-env\Scripts\repo.exe --version
.release-test-env\Scripts\repo.exe --help
.release-test-env\Scripts\repo.exe doctor
```

## Release Workflow & Trusted Publishing (OIDC)

Releases are published automatically through GitHub Actions (`.github/workflows/publish.yml`) using **PyPI Trusted Publishing (OIDC)**.

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          cache: pip
          python-version: "3.x"
      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build
      - name: Build package
        run: python -m build
      - name: Verify package metadata
        run: |
          python -m pip install twine
          twine check dist/*
      - name: Publish package distribution to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

> [!NOTE]
> Trusted Publishing leverages short-lived OpenID Connect (OIDC) JWT tokens issued directly by GitHub Actions to authenticate with PyPI. No long-lived PyPI API tokens (`PYPI_TOKEN`) or credentials are stored or needed.
