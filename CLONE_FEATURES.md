# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P1 - Spec diff mode to generate change-focused docs between two OpenAPI versions (new/changed/removed endpoints + schema deltas). (Impact 5/5, Effort 4/5, Strategic fit 5/5, Differentiation 4/5, Risk 3/5, Confidence 3/5)
- [x] P1 - Add `devex-agent lint` (or `--lint`) with baseline checks: unresolved refs, duplicate operation IDs, duplicate params, and unused components. (Delivered 2026-02-17)
- [ ] P1 - `--output-dir` mode to emit one docs file per tag plus an index page for large API surfaces. (Impact 4/5, Effort 4/5, Strategic fit 4/5, Differentiation 3/5, Risk 3/5, Confidence 3/5)
- [ ] P1 - HTML export theming flags (`--theme-color`, `--logo-url`, `--font-family`) without template forks. (Impact 4/5, Effort 3/5, Strategic fit 4/5, Differentiation 3/5, Risk 2/5, Confidence 3/5)
- [ ] P1 - Large-spec performance harness with reproducible benchmark fixture and target budget (render time/memory). (Impact 4/5, Effort 3/5, Strategic fit 4/5, Differentiation 2/5, Risk 2/5, Confidence 4/5)
- [ ] P2 - Incremental/cached rendering for `--watch` to avoid full re-render when unrelated sections change. (Impact 4/5, Effort 4/5, Strategic fit 4/5, Differentiation 2/5, Risk 3/5, Confidence 2/5)
- [ ] P2 - Opt-in external `http(s)` `$ref` bundling with explicit allowlist and timeout guards. (Impact 3/5, Effort 4/5, Strategic fit 3/5, Differentiation 2/5, Risk 4/5, Confidence 2/5)
- [ ] P2 - Improve schema example fidelity for bounds/constraints (`minimum`, `maximum`, `minLength`, `pattern`, `minItems`). (Impact 4/5, Effort 3/5, Strategic fit 4/5, Differentiation 3/5, Risk 2/5, Confidence 3/5)
- [ ] P2 - Improve `curl` examples for `multipart/form-data` and `application/x-www-form-urlencoded` requests. (Impact 4/5, Effort 3/5, Strategic fit 4/5, Differentiation 2/5, Risk 3/5, Confidence 3/5)
- [ ] P2 - Add dedicated tests for security combinations (multiple auth schemes, OR/AND requirements) in docs + curl output. (Impact 3/5, Effort 2/5, Strategic fit 4/5, Differentiation 2/5, Risk 2/5, Confidence 4/5)
- [ ] P2 - HTML accessibility hardening (skip links, keyboard nav, better contrast checks in CI). (Impact 3/5, Effort 3/5, Strategic fit 3/5, Differentiation 2/5, Risk 2/5, Confidence 3/5)
- [ ] P2 - Add release automation checks to enforce changelog entry and clean quality gate before tag creation. (Impact 3/5, Effort 2/5, Strategic fit 4/5, Differentiation 1/5, Risk 2/5, Confidence 4/5)
- [ ] P3 - Hosted docs preview mode for shareable review links (artifact upload or static host publish helper). (Impact 4/5, Effort 5/5, Strategic fit 3/5, Differentiation 3/5, Risk 4/5, Confidence 1/5)
- [ ] P3 - Optional interactive API console embed path for generated HTML (bring-your-own endpoint + auth placeholders). (Impact 3/5, Effort 5/5, Strategic fit 2/5, Differentiation 3/5, Risk 4/5, Confidence 1/5)
- [ ] P3 - Plugin/hooks system for custom endpoint render blocks without forking generator core. (Impact 3/5, Effort 5/5, Strategic fit 3/5, Differentiation 4/5, Risk 4/5, Confidence 1/5)
- [ ] P3 - Stdin input support (`devex-agent -`) for easier pipeline integration in CI/CD streams. (Impact 2/5, Effort 2/5, Strategic fit 3/5, Differentiation 1/5, Risk 2/5, Confidence 4/5)

## Implemented
- [x] 2026-02-17 - Add `--lint` mode with baseline OpenAPI checks: unresolved `$ref`, duplicate `operationId`, duplicate parameters, and unused components.
  - Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/test_cli.py`, `tests/fixtures/lint_issues.yaml`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/petstore.yaml --lint`, local `.venv/bin/devex-agent tests/fixtures/lint_issues.yaml --lint`.
- [x] 2026-02-11 - Enforce OpenAPI parameter override semantics: operation-level parameters now override path-level parameters by `(name, in)`, preventing duplicate parameter rows and stale `curl` query values.
  - Evidence: `src/devex_agent/generator.py`, `tests/test_generator.py`, `tests/fixtures/param_override.yaml`, commit `fac4526`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/param_override.yaml --output /tmp/devex-cycle1-smoke.G1xu5q/param.md`.
- [x] 2026-02-11 - Fix internal `$ref` resolution and strict validation for escaped JSON Pointer segments (`~1`, `~0`) so component names containing `/` or `~` resolve correctly.
  - Evidence: `src/devex_agent/generator.py`, `tests/test_generator.py`, `tests/test_cli.py`, `tests/fixtures/escaped_ref.yaml`, commit `fac4526`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/escaped_ref.yaml --strict --output /tmp/devex-cycle1-smoke.G1xu5q/escaped.md`.
- [x] 2026-02-11 - Add fail-fast CLI validation for `--watch --interval` to reject non-positive values with a stable user-facing error.
  - Evidence: `src/devex_agent/cli.py`, `tests/test_cli.py`, commit `fac4526`, local `make check`.
- [x] 2026-02-10 - `--serve` mode for generated HTML: start a local static server for the output file (supports `--host`, `--port`, and optional `--watch` rebuild).
  - Evidence: `src/devex_agent/cli.py`, `tests/test_cli.py`, commit `9a66b33`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/petstore.yaml --output /tmp/devex-serve-smoke/API.html --serve --host 127.0.0.1 --port <free_port>` + `curl http://127.0.0.1:<free_port>/API.html` (contains `<!doctype html>`).
- [x] 2026-02-10 - Schema example fidelity: support `default`, JSON Schema `const`, and `additionalProperties` (map/dict schemas) during example generation.
  - Evidence: `src/devex_agent/generator.py`, commit `76beb21`, local `make check`.
- [x] 2026-02-10 - Add fixtures/tests for `default`/`const`/`additionalProperties` schema example generation (protect against regressions across real-world specs).
  - Evidence: `tests/test_generator.py`, `tests/fixtures/schema_defaults.yaml`, commit `76beb21`, local `.venv/bin/devex-agent tests/fixtures/schema_defaults.yaml --output /tmp/devex-schema-defaults-smoke.md`.
- [x] 2026-02-09 - Multi-file specs (local): add `--bundle` to inline external file `$ref` so split OpenAPI specs render cleanly (and can be paired with `--strict`).
  - Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/test_cli.py`, `tests/fixtures/multi_file_root.yaml`, `tests/fixtures/multi_file_schemas.yaml`, commit `48d599b`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/multi_file_root.yaml --bundle --strict --output /tmp/devex-bundle-smoke.md`.
- [x] 2026-02-09 - `$ref` siblings overlay for docs rendering: preserve doc-friendly overrides like `example` during internal ref resolution.
  - Evidence: `src/devex_agent/generator.py`, `tests/test_generator.py`, `tests/fixtures/ref_siblings.yaml`, commit `48d599b`, local `make check`.
- [x] 2026-02-09 - Docs alignment: document `--bundle` and refresh roadmap/plan/project tracker to reflect current shipped behavior and next steps.
  - Evidence: `README.md`, `docs/ROADMAP.md`, `docs/PROJECT.md`, `PLAN.md`, `docs/CHANGELOG.md`, `PROJECT_MEMORY.md`, `CLONE_FEATURES.md`, commit `a4a5c16`, local `make check`, CI run `21845795567` (success).
- [x] 2026-02-09 - Add `--strict` mode: fail generation on unresolved `$ref` and unsupported request/response body content types (supported: JSON and `*+json`).
  - Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/test_cli.py`, `tests/test_generator.py`, `tests/fixtures/unresolved_ref.yaml`, `tests/fixtures/unsupported_content_type.yaml`, commit `87af3f0`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/petstore.yaml --strict --output /tmp/devex-strict-ok.md`.
- [x] 2026-02-09 - HTML UX polish: active nav highlight, shareable deep links (filter preserved in URL hash), and copy-link buttons for tags/endpoints.
  - Evidence: `src/devex_agent/generator.py`, `tests/test_generator.py`, commit `d7d950e`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/petstore.yaml --output /tmp/devex-html-ux.html`.
- [x] 2026-02-09 - Hardened CLI errors and made server selection discoverable via `--list-servers`.
  - Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/test_cli.py`, commit `a3ac5cd`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/servers.yaml --list-servers`.
- [x] 2026-02-09 - Refreshed docs to reduce onboarding friction and reflect shipped CLI behavior.
  - Evidence: `README.md`, `docs/ROADMAP.md`, `docs/PROJECT.md`, `PLAN.md`, `AGENTS.md`, commit `ab5dcf5`, CI run `21830124938` (success).
- [x] 2026-02-09 - Versioned the autonomous operating contract and session task list in-repo.
  - Evidence: `AGENTS.md`, `CLONE_FEATURES.md`, commit `1e12b18`, CI run `21814422097` (success).
- [x] 2026-02-09 - Discriminator-aware `oneOf`/`anyOf` example generation (avoid null variants; include discriminator property when possible).
  - Evidence: `src/devex_agent/generator.py`, `tests/fixtures/oneof_discriminator.yaml`, `tests/test_generator.py`, commit `7d9f782`, CI run `21814471218` (success), local `make check`, local `.venv/bin/devex-agent tests/fixtures/oneof_discriminator.yaml --output /tmp/devex-oneof.md`.
- [x] 2026-02-09 - HTML export with a minimal theme and static endpoint filter/search (roadmap near-term item).
  - Evidence: `src/devex_agent/generator.py`, `src/devex_agent/cli.py`, `pyproject.toml`, `tests/test_generator.py`, `README.md`, commit `3140685`, CI run `21814568335` (success), local `make check`, local `.venv/bin/devex-agent tests/fixtures/petstore.yaml --format html --output /tmp/devex-agent-smoke.html`.
- [x] 2026-02-09 - CI-safe `Makefile` execution for both local `.venv` and CI/global environments.
  - Evidence: `Makefile`, commit `4cc9482`, CI run `21808754489` (success), local `make check`, local `PATH="$(pwd)/.venv/bin:$PATH" make check VENV=.missing`.
- [x] 2026-02-09 - Resolved referenced `requestBody` objects and response refs during render.
  - Evidence: `src/devex_agent/generator.py`, `tests/fixtures/request_body_ref.yaml`, `tests/test_generator.py`, commit `727ef02`.
- [x] 2026-02-09 - Hardened operation collection against malformed path items/operations.
  - Evidence: `src/devex_agent/generator.py`, `tests/fixtures/malformed_paths.yaml`, `tests/test_generator.py`, commit `727ef02`.
- [x] 2026-02-09 - Synchronized docs with real CLI invocation and maintenance release notes.
  - Evidence: `README.md`, `docs/PLAN.md`, `docs/CHANGELOG.md`.
- [x] 2026-02-09 - Added persistent maintenance memory and incident tracking files.
  - Evidence: `PROJECT_MEMORY.md`, `INCIDENTS.md`.
- [x] 2026-02-09 - Executed CLI smoke verification path and captured output evidence.
  - Evidence: `devex-agent tests/fixtures/petstore.yaml --output /tmp/devex-agent-smoke.md`, grep checks on `/tmp/devex-agent-smoke.md`.
- [x] 2026-02-09 - Reduce CLI friction: infer format from `--output` extension; accept `devex-agent generate <spec>` compatibility alias.
  - Evidence: `src/devex_agent/cli.py`, `tests/test_cli.py`, commit `e759ed6`, local `make check`.
- [x] 2026-02-09 - Base URL controls: `--server` selection, `--base-url` override, and server-variable expansion for stable `curl` URLs.
  - Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/fixtures/servers.yaml`, `tests/test_generator.py`, commit `6e51670`, local `.venv/bin/devex-agent tests/fixtures/servers.yaml --server 1 --output /tmp/devex-agent-servers.md`.
- [x] 2026-02-09 - Align `devex_agent.__version__` with the packaged version; refresh roadmap and README to match shipped behavior.
  - Evidence: `src/devex_agent/__init__.py`, `docs/ROADMAP.md`, `README.md`, commit `ef52e29`.
- [x] 2026-02-09 - Verified GitHub Actions CI remains green after Cycle 2 changes.
  - Evidence: CI run `21822490037` (success) on `main`.

## Insights
- Session scoring (2026-02-11): top 5 high-impact candidates were spec diff mode, lint mode, per-tag output mode, HTML theming controls, and large-spec performance harness; this cycle executed the highest-confidence reliability slice first (trusted: local code/tests).
- Quick code review sweep (2026-02-11): parameter override semantics and escaped JSON Pointer refs were correctness risks with low effort and high confidence, so they were prioritized ahead of larger feature work (trusted: local code/tests).
- Market scan (bounded, 2026-02-11, untrusted): baseline expectations still center on static HTML generation, search/navigation, and easy local preview in doc CLIs. Source: https://redocly.com/docs/cli/commands/build-docs
- Market scan (bounded, 2026-02-11, untrusted): interactive API docs commonly expose "Try it out"/API client flows, which remains a differentiation opportunity for DevEx Agent. Source: https://swagger.io/tools/swagger-ui/download/
- Market scan (bounded, 2026-02-11, untrusted): modern API docs platforms emphasize built-in API clients, multi-theme UX, and flexible embeddings. Source: https://scalar.com/docs
- Gap map refresh (2026-02-11):
  - Missing: spec diff mode, lint mode, optional interactive console path.
  - Weak: large-spec performance tooling, configurable HTML theming, multipart form curl examples.
  - Parity: strict mode, local-file bundling, HTML export/filter/deep links, local preview server.
  - Differentiator: schema/example heuristics plus resilient/friendly CLI failure behavior.
- CI failures across runs `21557668393` through `21557307241` shared the same root cause: `make check` assumed `.venv` activation.
- On macOS, `python` may not exist (only `python3`), so docs should default to `python3 -m venv ...` for a smoother quickstart.
- Typer is currently exposing single-command mode (`devex-agent <spec> ...`); accept `devex-agent generate <spec> ...` as a compatibility alias.
- Regression coverage improved by adding fixtures for referenced request bodies and malformed path definitions.
- Market scan (bounded, 2026-02-09): baseline expectations for OpenAPI doc generators include static HTML export, theming, and built-in search or endpoint navigation; many tools also offer interactive "try it" consoles and spec bundling/linting.
- Market scan source: Redocly CLI `build-docs` (static HTML output, theming/search options) https://redocly.com/docs/cli/commands/build-docs
- Market scan source: Swagger UI (interactive browsing + "Try it out") https://github.com/swagger-api/swagger-ui
- Market scan source: Stoplight Elements (embeddable components, "Try It") https://stoplight.io/open-source/elements
- Market scan (bounded, 2026-02-09): many doc platforms support multiple OpenAPI specs, interactive "try it" panels, and multiple-server selection; DevEx Agent should prioritize low-friction static artifacts and accurate base URLs.
- Market scan source: Mintlify OpenAPI setup (multiple specs; interactive docs; `$ref` internal-only) https://www.mintlify.com/docs/api-playground/openapi-setup
- Market scan source: Docusaurus OpenAPI plugin (static generation + demo panel) https://github.com/cloud-annotations/docusaurus-openapi
- Market scan (bounded, 2026-02-09): “strictness” and linting are first-class in adjacent tooling (unresolved `$ref` and unused components are common baseline checks in CLI linters). https://redocly.com/docs/cli/rules/built-in-rules
- Market scan (bounded, 2026-02-09): multi-file specs and bundling/dereferencing are common needs; several CLIs explicitly support bundling OpenAPI specs into a single artifact. https://github.com/APIDevTools/swagger-cli
- Market scan (bounded, 2026-02-09): interactive “Try It” consoles + multi-server selection are a common UX expectation in interactive doc components. https://stoplight.io/open-source/elements
- Market scan (bounded, 2026-02-09): multi-file OpenAPI support often centers on "bundle" workflows that follow `$ref` to produce a single-file artifact; some tools also support fully dereferenced bundles (`$ref` eliminated) and removing unused components. https://redocly.com/docs/cli/commands/bundle
- Market scan (bounded, 2026-02-09): modern OpenAPI UI components emphasize instant search, multiple themes, and an embedded API client beyond basic "try it out". https://scalar.com/guides/migration/swagger-ui
- Market scan (bounded, 2026-02-09): interactive docs commonly include an API console and easy theming/branding without custom template forks. https://rapidocweb.com/index.html
- Market scan (bounded, 2026-02-09): bundling in the ecosystem often relies on `$ref` parser libraries with CLI wrappers (e.g. swagger-cli) used across tooling stacks. https://blog.stoplight.io/keeping-openapi-dry-and-portable
- Market scan (bounded, 2026-02-10): local docs preview servers with `--host`/`--port` options are baseline parity in adjacent CLIs; DevEx Agent should support a minimal local preview loop that serves the generated HTML artifact. https://redocly.com/docs/cli/v1/commands/preview-docs
- Gap map (2026-02-09):
  - Missing (strategic): diff mode, interactive “try it” console (untrusted: based on external market scan).
  - Weak: very-large-spec UX/perf (pagination/incremental render), richer theming controls for HTML.
  - Parity: static single-file HTML export with navigation + filter, stable Base URL selection, fail-fast strict validation, and multi-file (local) `$ref` bundling (trusted: local code/tests).
  - Differentiator: schema-example fidelity heuristics (discriminator-aware `oneOf`/`anyOf`, `allOf` merge) and production-grade CLI error UX (trusted: local code/tests).

## Notes
- This file is maintained by the autonomous clone loop.

### Auto-discovered Open Checklist Items (2026-02-09)
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] `make check`
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Update `docs/CHANGELOG.md`
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Tag release (SemVer)
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Create GitHub Release with notes
