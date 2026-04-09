# ADR-010: uv as the Development Workflow Tool

**Status:** Accepted
**Date:** 2026-04-09

## Context

The project needed a development workflow tool for managing virtual environments, installing dependencies, and running tests. The main options considered were pip + venv, Poetry, and uv.

**pip + venv** is the baseline but requires multiple commands and no lock file support by default. **Poetry** is mature but uses its own pyproject.toml extensions, its own lock format, and its own build backend — locking the project into Poetry-specific conventions.

**uv** is a Python package manager and project tool written in Rust by Astral (the ruff team). Key characteristics:
- 10–100x faster than pip for installs and dependency resolution
- Works with standard `pyproject.toml` and any PEP 517 build backend — no lock-in
- Replaces pip, pip-tools, venv, and virtualenv in a single binary
- Supports PEP 735 `[dependency-groups]` for dev dependencies
- Generates a `uv.lock` file for reproducible installs
- Can manage Python versions, removing the need for a separate pyenv
- Rapidly becoming the standard in the Python ecosystem (2025–2026)

## Decision

Use uv as the development workflow tool. The build backend remains hatchling — uv is the installer and environment manager, not the build system. This separation of concerns is intentional.

**Key commands:**
```bash
uv sync                    # create .venv and install all deps
uv sync --group dev        # include dev dependencies
uv run pytest tests/       # run tests inside the managed venv
uv add --dev <package>     # add a dev dependency
uv lock                    # regenerate uv.lock after manual pyproject.toml edits
```

The `uv.lock` file is committed to the repository so all contributors get identical dev environments.

## Consequences

- Contributors need uv installed (`brew install uv` / `pip install uv` / `curl` installer)
- `pyproject.toml` uses `[dependency-groups]` (PEP 735) instead of `[project.optional-dependencies]` for dev deps — this is uv's recommended format and not compatible with plain pip's `-e ".[dev]"` syntax
- The `.venv/` directory is created by uv in the project root and is gitignored
- Install time for new contributors is significantly faster than with pip
- The hatchling build backend is unchanged — `pip install qgis-bridge` continues to work for end users who don't use uv
