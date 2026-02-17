# Project Memory

## Recent Decisions (Cycle 2 - 2026-02-17)
- 2026-02-17 | Implemented `--lint` mode as the highest-impact pending reliability feature, with baseline checks for unresolved refs, duplicate operation IDs, duplicate parameters, and unused components. | Why: strongest CI/release guardrail value with low operational risk and clear user-facing output. | Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/test_cli.py`, `tests/fixtures/lint_issues.yaml`, local `make check`, local lint smoke path. | Commit: pending | Confidence: High | Trust label: trusted (local code/tests)
- 2026-02-17 | Calibrated lint scope to proven ecosystem baseline (Redocly/Spectral/OpenAPI spec semantics) while treating external guidance as untrusted input. | Why: align first lint slice with common operator expectations without over-extending rule complexity in one change. | Evidence: Redocly CLI lint docs, Stoplight Spectral docs, OpenAPI specification sections for `operationId` uniqueness and parameter uniqueness. | Commit: pending | Confidence: Medium | Trust label: untrusted (external web)

## Verification Evidence (Cycle 2 - 2026-02-17)
- `.venv/bin/pytest tests/test_cli.py -q` | Pass | 19 CLI tests passed, including new lint pass/fail coverage.
- `make check` | Pass | `ruff`, `mypy`, `pytest` (40 passed), `bandit`, and package build all succeeded.
- `set -e; .venv/bin/devex-agent tests/fixtures/petstore.yaml --lint; set +e; .venv/bin/devex-agent tests/fixtures/lint_issues.yaml --lint > /tmp/devex-lint-smoke.txt; exit_code=$?; set -e; printf "lint_issues_exit=%s\n" "$exit_code"; rg -n "duplicate-operation-id|duplicate-parameter|unresolved-ref|unused-component" /tmp/devex-lint-smoke.txt` | Pass | Valid spec exits 0; invalid fixture exits 2 with all expected lint rule identifiers.

## Recent Decisions (Cycle 1 - 2026-02-11)
- 2026-02-11 | Prioritized reliability fixes over larger feature work: enforce OpenAPI parameter override semantics, support escaped JSON Pointer refs, and validate watch interval input. | Why: highest impact-to-effort for production correctness with low regression risk. | Evidence: `src/devex_agent/generator.py`, `src/devex_agent/cli.py`, `tests/test_generator.py`, `tests/test_cli.py`, `tests/fixtures/param_override.yaml`, `tests/fixtures/escaped_ref.yaml`, local `make check`, local CLI smoke path. | Commit: `fac4526` | Confidence: High | Trust label: trusted (local code/tests)
- 2026-02-11 | Refreshed market-scan expectations but treated all external findings as non-authoritative input only. | Why: reduce prompt-injection and competitor-bias risk while still informing gap mapping. | Evidence: Redocly docs (`build-docs`), Swagger UI docs page, Scalar docs page; summarized in `CLONE_FEATURES.md`. | Commit: `75a41b5` | Confidence: Medium | Trust label: untrusted (external web)
- 2026-02-11 | Selected next strategic direction: spec diff mode and lint mode remain top roadmap candidates after this reliability cycle. | Why: strongest PMF leverage for CI/release workflows and doc drift prevention. | Evidence: scoring list under `CLONE_FEATURES.md` Candidate Features To Do. | Commit: `75a41b5` | Confidence: Medium-High | Trust label: trusted (repo strategy + local analysis)

## Mistakes And Fixes (Cycle 1 - 2026-02-11)
- 2026-02-11 | Mistake: used a brittle `jq` filter while polling GitHub Actions runs and hit a type error (`startswith()` on non-string input). | Root cause: over-assumed JSON field types in one-off CLI query. | Fix: switched to direct `gh run list` output inspection by exact SHA. | Prevention rule: for CI polling commands, avoid type-sensitive `jq` transforms unless field types are explicitly guarded.

## Verification Evidence (Cycle 1 - 2026-02-11)
- `make check` | Pass | `ruff`, `mypy`, `pytest` (36 passed), `bandit`, and package build all succeeded.
- `smoke_dir="$(mktemp -d /tmp/devex-cycle1-smoke.XXXXXX)"; .venv/bin/devex-agent tests/fixtures/param_override.yaml --output "$smoke_dir/param.md"; rg -n "\\| lang \\| query \\|" "$smoke_dir/param.md"; rg -n "lang=fr" "$smoke_dir/param.md"; .venv/bin/devex-agent tests/fixtures/escaped_ref.yaml --strict --output "$smoke_dir/escaped.md"; rg -n '"id": "string"' "$smoke_dir/escaped.md"; rg -n '"state": "string"' "$smoke_dir/escaped.md"` | Pass | Verified override behavior and escaped-ref strict rendering path.
- `gh issue list --limit 50 --state open --json number,title,author,url` | Pass | Returned `[]`; no owner/bot-authored open issues to prioritize.
- `gh run list --limit 20 --json databaseId,headSha,status,conclusion,workflowName,url,createdAt` | Pass | Run `21895227275` for `fac4526` completed with `success`.
- `for i in {1..30}; do gh run view 21895272830 --json status,conclusion,url,headSha; done` (polled until completion) | Pass | Run `21895272830` for `75a41b5` completed with `success`.

## Entry 2026-02-10 - Local HTML preview server (`--serve`)
- Decision: Add `--serve` mode to start a local static server for generated HTML output (with `--host`/`--port`, and compatible with `--watch` rebuilds).
- Why: Static HTML is much more useful when it can be previewed locally without extra tooling; parity with adjacent OpenAPI doc CLIs typically includes a local preview loop.
- Evidence:
  - Commit: `9a66b33`
  - Files:
    - `src/devex_agent/cli.py`
    - `tests/test_cli.py`
  - Local verification:
    - `make check` (pass)
    - Smoke (pass):
      ```bash
      workdir="$(mktemp -d /tmp/devex-serve-smoke2.XXXXXX)"
      port="$(
        python3 - <<'PY'
      import socket
      s = socket.socket()
      s.bind(("127.0.0.1", 0))
      print(s.getsockname()[1])
      s.close()
      PY
      )"

      PYTHONUNBUFFERED=1 .venv/bin/devex-agent tests/fixtures/petstore.yaml \
        --output "$workdir/API.html" \
        --serve --host 127.0.0.1 --port "$port" \
        >"$workdir/serve.log" 2>&1 &
      pid=$!

      curl -fsS --max-time 2 "http://127.0.0.1:$port/API.html" | rg "<!doctype html>"

      kill -TERM "$pid"
      ```
  - CI verification:
    - Run `21855127232` (success)
- Confidence: High
- Trust Label: Verified (tests + smoke + CI)
- Follow-ups:
  - Consider adding graceful SIGTERM shutdown for `--serve` if this becomes a common workflow in scripts.

## Entry 2026-02-10 - Schema example fidelity: `default`, `const`, `additionalProperties`
- Decision: Improve schema example generation to prefer JSON Schema `const`, then `default`, and to emit representative map examples for object schemas with `additionalProperties` (plus include a small number of optional fields with strong example/default signals).
- Why: Real-world OpenAPI specs frequently rely on `default`/`const` and map-like schemas; examples that ignore these signals are less useful and can look incorrect.
- Evidence:
  - Commit: `76beb21`
  - Files:
    - `src/devex_agent/generator.py`
    - `tests/test_generator.py`
    - `tests/fixtures/schema_defaults.yaml`
  - Local verification:
    - `make check` (pass)
    - Smoke (pass):
      - `.venv/bin/devex-agent tests/fixtures/schema_defaults.yaml --output /tmp/devex-schema-defaults-smoke.md`
      - `rg -n '"status": "ok"' /tmp/devex-schema-defaults-smoke.md`
      - `rg -n '"count": 7' /tmp/devex-schema-defaults-smoke.md`
      - `rg -n '"key": 0' /tmp/devex-schema-defaults-smoke.md`
  - CI verification:
    - Run `21855123791` (success)
- Confidence: High
- Trust Label: Verified (tests + smoke + CI)
- Follow-ups:
  - Extend example heuristics further as new fixtures come in (formats, min/max bounds, nested maps).

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

## Entry 2026-02-09 - CLI friction reduction and accurate Base URL controls
- Decision:
  - Infer output format from `--output` extension when `--format` is omitted.
  - Accept `devex-agent generate <spec>` as a compatibility alias while keeping single-command mode (`devex-agent <spec> ...`).
  - Add Base URL controls (`--server`, `--base-url`) and expand OpenAPI server URL variables using defaults.
  - Align `devex_agent.__version__` with the packaged version.
- Why:
  - Reduce CLI friction and make HTML export feel "obvious".
  - Improve correctness of `curl` examples when OpenAPI specs define multiple servers or templated server URLs.
- Evidence:
  - Commits: `e759ed6`, `6e51670`, `ef52e29`
  - Files:
    - `src/devex_agent/cli.py`
    - `src/devex_agent/generator.py`
    - `src/devex_agent/__init__.py`
    - `tests/test_cli.py`
    - `tests/test_generator.py`
    - `tests/fixtures/servers.yaml`
    - `README.md`
    - `docs/ROADMAP.md`
  - Local verification:
    - `make check` (pass; 18 tests)
    - `.venv/bin/devex-agent tests/fixtures/petstore.yaml --output /tmp/devex-agent-smoke.html` (pass; HTML inferred)
    - `.venv/bin/devex-agent tests/fixtures/servers.yaml --server 1 --output /tmp/devex-agent-servers.md` (pass; Base URL uses expanded variables)
  - CI verification:
    - Run `21822490037` (success)
- Confidence: High
- Trust Label: Verified (tests + smoke)
- Follow-ups:
  - Consider adding `--list-servers` (or richer error output) for specs with multiple servers.

## Entry 2026-02-09 - CLI discoverability and failure-mode UX
- Decision:
  - Add `--list-servers` to print expanded OpenAPI `servers` URLs and exit.
  - Emit friendly errors with stable exit codes for common failures (missing spec file, invalid JSON/YAML, URL fetch failures).
- Why:
  - Make `--server` selection discoverable and reduce “guesswork”.
  - Avoid Python tracebacks for expected user errors and make CLI usage more predictable in automation.
- Evidence:
  - Commit: `a3ac5cd`
  - Files:
    - `src/devex_agent/cli.py`
    - `src/devex_agent/generator.py`
    - `tests/test_cli.py`
  - Local verification:
    - `make check` (pass; 21 tests)
    - `.venv/bin/devex-agent tests/fixtures/servers.yaml --list-servers` (pass; prints expanded URLs)
    - `.venv/bin/devex-agent https://raw.githubusercontent.com/sarveshkapre/devex-agent/main/tests/fixtures/petstore.yaml --output /tmp/devex-agent-url.md` (pass; URL fetch path)
  - CI verification:
    - Run `21830046340` (success)
- Confidence: High
- Trust Label: Verified (tests + smoke + CI)

## Entry 2026-02-09 - Docs alignment and onboarding friction reduction
- Decision:
  - Update quickstart to default to `python3` (macOS-friendly).
  - Document `--list-servers` alongside `--server` / `--base-url`.
  - Refresh roadmap/project docs to reflect shipped behavior and current next steps.
- Why:
  - Reduce first-run friction and keep docs aligned with the CLI’s real capabilities.
- Evidence:
  - Commit: `ab5dcf5`
  - Files:
    - `README.md`
    - `docs/ROADMAP.md`
    - `docs/PROJECT.md`
    - `PLAN.md`
    - `AGENTS.md`
    - `CLONE_FEATURES.md`
  - Local verification:
    - `make check` (pass; 21 tests)
  - CI verification:
    - Run `21830124938` (success)
- Confidence: High
- Trust Label: Verified (local + CI)

## Entry 2026-02-09 - Strict mode for refs and content types
- Decision: Add `--strict` mode to fail generation on unresolved `$ref` and unsupported request/response content types (supported: `application/json`, `application/*+json`).
- Why: DevEx Agent is often run in CI or release pipelines; best-effort rendering can mask broken specs and produce misleading examples when bodies aren’t JSON.
- Evidence:
  - Commits: `87af3f0`
  - Files:
    - `src/devex_agent/cli.py`
    - `src/devex_agent/generator.py`
    - `tests/test_cli.py`
    - `tests/test_generator.py`
    - `tests/fixtures/unresolved_ref.yaml`
    - `tests/fixtures/unsupported_content_type.yaml`
    - `README.md`
    - `docs/ROADMAP.md`
    - `docs/PROJECT.md`
    - `docs/CHANGELOG.md`
  - Local verification:
    - `make check` (pass; 26 tests)
    - `.venv/bin/devex-agent tests/fixtures/petstore.yaml --strict --output /tmp/devex-strict-ok.md` (pass)
    - `.venv/bin/devex-agent tests/fixtures/unresolved_ref.yaml --strict --output /tmp/devex-strict-fail.md` (exit 2; prints unresolved `$ref`)
    - `.venv/bin/devex-agent tests/fixtures/unsupported_content_type.yaml --strict --output /tmp/devex-strict-fail2.md` (exit 2; prints unsupported content type)
- Confidence: High
- Trust Label: Verified (tests + smoke)

## Entry 2026-02-09 - HTML export: deep links, active nav, copy links
- Decision: Improve the HTML export UX by making deep links shareable (preserve filter query in URL hash), highlighting the active nav item, and adding “Copy link” buttons for tags/endpoints.
- Why: A static HTML artifact is only useful if it’s easy to navigate and share. Persisting filter state + stable deep links reduces friction in reviews and docs handoffs.
- Evidence:
  - Commits: `d7d950e`
  - Files:
    - `src/devex_agent/generator.py`
    - `tests/test_generator.py`
    - `README.md`
    - `docs/CHANGELOG.md`
  - Local verification:
    - `make check` (pass; 26 tests)
    - `.venv/bin/devex-agent tests/fixtures/petstore.yaml --output /tmp/devex-html-ux.html` (pass)
    - `rg -n 'href=\"#op=|URLSearchParams|copylink' /tmp/devex-html-ux.html` (pass; confirms deep-link format + JS)
- Confidence: Medium-High
- Trust Label: Verified (tests + smoke)

## Entry 2026-02-09 - Multi-file spec support via `--bundle`
- Decision:
  - Add `--bundle` to inline external *local file* `$ref` so split OpenAPI specs can be rendered as a single logical spec.
  - Overlay `$ref` siblings (e.g. `example`) during internal ref resolution to preserve doc-friendly overrides commonly used in real-world specs.
- Why:
  - Many OpenAPI specs are split across files (schemas/parameters) and fail strict validation or render poorly without a bundling step.
  - `$ref` siblings are frequently used to override examples/descriptions for documentation, even if the formal spec semantics treat them as ignored.
- Evidence:
  - Commit: `48d599b`
  - Files:
    - `src/devex_agent/cli.py`
    - `src/devex_agent/generator.py`
    - `tests/test_cli.py`
    - `tests/test_generator.py`
    - `tests/fixtures/multi_file_root.yaml`
    - `tests/fixtures/multi_file_schemas.yaml`
    - `tests/fixtures/ref_siblings.yaml`
  - Local verification:
    - `make check` (pass)
    - `.venv/bin/devex-agent tests/fixtures/multi_file_root.yaml --bundle --strict --output /tmp/devex-bundle-smoke.md` (pass)
    - `rg -n '\"kind\": \"dog\"|\"id\": \"string\"' /tmp/devex-bundle-smoke.md` (pass)
- Confidence: Medium-High
- Trust Label: Verified (tests + smoke)
- Follow-ups:
  - Consider opt-in support for URL-based `$ref` (with safe defaults) only if there is a strong user need.
  - If bundling grows, revisit deduplication/perf for very large shared component graphs.

## Mistakes And Fixes
- 2026-02-09 - Mistake: assumed Typer required explicit subcommands and briefly implemented an unnecessary console-script wrapper.
  - Fix: validated actual CLI shape with `CliRunner` and implemented a compatibility alias (`generate` prefix) without changing the entrypoint.
  - Prevention rule: add/keep a focused CLI invocation test before changing CLI dispatch/entrypoint behavior.
