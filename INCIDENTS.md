# Incidents

## Incident 2026-02-09 - CI quality gate failed on all pushes
- Status: Resolved
- Severity: Medium
- Detection:
  - GitHub Actions `ci` workflow failures on `main` (for example runs `21557668393`, `21557634924`).
- Impact:
  - All `build` jobs failed at `make check`, blocking confidence in release quality and hiding downstream audit results.
- Root Cause:
  - `Makefile` targets assumed a local virtualenv and executed `. .venv/bin/activate` in every command.
  - CI job installs dependencies globally and does not create `.venv`, so shell activation failed immediately.
- Resolution:
  - Updated `Makefile` to use `.venv/bin/*` tools only when `.venv` exists, otherwise use `PATH` tools.
  - Verified with:
    - `make check`
    - `PATH="$(pwd)/.venv/bin:$PATH" make check VENV=.missing`
    - GitHub Actions run `21808754489` (success)
- Prevention Rules:
  - Build and test commands must not assume local shell activation state.
  - Verify any build-tooling change in both local-venv and CI-like execution modes.
  - Keep a CI smoke run check after each push that changes automation or developer tooling.
