# Project Memory

## Entry 2026-02-09 - CI execution environment mismatch
- Decision: Make `Makefile` commands run against `.venv` when present, otherwise fall back to tools available on `PATH`.
- Why: GitHub Actions installs dependencies globally for jobs, so hard-coded activation of `.venv/bin/activate` caused `make check` to fail immediately.
- Evidence:
  - Commit: `4cc9482`
  - File: `Makefile`
  - Local verification:
    - `make check` (pass)
    - `PATH="$(pwd)/.venv/bin:$PATH" make check VENV=.missing` (pass, CI-like mode)
  - CI verification:
    - Run `21808754489` (success)
- Confidence: High
- Trust Label: Verified (local + CI)
- Follow-ups:
  - Keep `make` targets environment-agnostic.
  - Re-check CI whenever build tooling changes.

## Entry 2026-02-09 - Generator robustness for references and malformed input
- Decision: Resolve `$ref` for `requestBody`/response objects during render and skip malformed path items/operations while collecting operations.
- Why: Referenced request bodies rendered without examples/payloads, and malformed path values could cause runtime errors during generation.
- Evidence:
  - Commit: `727ef02`
  - Files:
    - `src/devex_agent/generator.py`
    - `tests/test_generator.py`
    - `tests/fixtures/request_body_ref.yaml`
    - `tests/fixtures/malformed_paths.yaml`
  - Local verification:
    - `make check` (pass; 9 tests)
- Confidence: High
- Trust Label: Verified (tests)
- Follow-ups:
  - Extend reference resolution coverage to additional OpenAPI components when new edge cases are discovered.
