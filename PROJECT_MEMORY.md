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

## Entry 2026-02-09 - Version the autonomous contract in-repo
- Decision: Add `AGENTS.md` to the repository and keep the session task list in `CLONE_FEATURES.md` current.
- Why: The autonomous loop needs an auditable, versioned operating contract that ships with the repo and can be enforced by CI/process.
- Evidence:
  - Commit: `1e12b18`
  - Files:
    - `AGENTS.md`
    - `CLONE_FEATURES.md`
  - CI verification:
    - Run `21814422097` (success)
- Confidence: High
- Trust Label: Verified (git + CI)
- Follow-ups:
  - Keep `AGENTS.md` immutable core rules stable; only update mutable facts/date when needed.

## Entry 2026-02-09 - Discriminator-aware `oneOf`/`anyOf` examples
- Decision: Improve schema example generation for `oneOf`/`anyOf` by selecting a stable non-null variant, preferring discriminator mappings when present, and injecting the discriminator property value into object examples when possible.
- Why: Naively choosing the first variant often yields unhelpful or incorrect examples (especially when a `null` variant is listed first or polymorphism uses discriminators).
- Evidence:
  - Commit: `7d9f782`
  - Files:
    - `src/devex_agent/generator.py`
    - `tests/fixtures/oneof_discriminator.yaml`
    - `tests/test_generator.py`
  - Local verification:
    - `make check` (pass; 11 tests)
    - `.venv/bin/devex-agent tests/fixtures/oneof_discriminator.yaml --output /tmp/devex-oneof.md` (pass; example contains `petType=cat` + `huntingSkill`)
  - CI verification:
    - Run `21814471218` (success)
- Confidence: High
- Trust Label: Verified (tests + smoke + CI)
- Follow-ups:
  - Revisit selection heuristics if real-world specs show better signals (e.g. `x-discriminator-value`, vendor extensions).

## Entry 2026-02-09 - HTML export with static endpoint filter
- Decision: Add `--format html` output that generates a single self-contained HTML file with a minimal theme and client-side endpoint filtering.
- Why: Markdown is great for repos, but many teams want a shareable, readable HTML artifact with navigation and quick search/filter.
- Evidence:
  - Commit: `3140685`
  - Files:
    - `src/devex_agent/generator.py`
    - `src/devex_agent/cli.py`
    - `pyproject.toml`
    - `tests/test_generator.py`
    - `README.md`
  - Local verification:
    - `make check` (pass; 12 tests)
    - `.venv/bin/devex-agent tests/fixtures/petstore.yaml --format html --output /tmp/devex-agent-smoke.html` (pass; contains search input + endpoint nav)
  - CI verification:
    - Run `21814568335` (success)
- Confidence: Medium-High
- Trust Label: Verified (tests + smoke)
- Follow-ups:
  - Consider `--format auto` or output-extension inference (`.md` vs `.html`) to reduce CLI friction.
