# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P2 (Cycle 3) - Add `--strict` mode: fail generation if `$ref` cannot be resolved, or if request/response bodies can’t be rendered for a supported content type. (Impact 3/5, Effort 3/5, Strategic fit 4/5, Differentiation 2/5, Risk 3/5, Confidence 3/5)
- [ ] P2 - Improve HTML UX: highlight active nav item, preserve search state in URL hash, and add a “copy anchor link” affordance for endpoints. (Impact 3/5, Effort 3/5, Strategic fit 3/5, Differentiation 2/5, Risk 2/5, Confidence 3/5)
- [ ] P2 - Add spec diff mode to generate change-focused docs between two versions. (Impact 3/5, Effort 4/5, Strategic fit 3/5, Differentiation 3/5, Risk 3/5, Confidence 2/5)
- [ ] P2 - Add multi-file spec merging support for split OpenAPI specs (roadmap later item). (Impact 4/5, Effort 4/5, Strategic fit 4/5, Differentiation 3/5, Risk 4/5, Confidence 2/5)
- [ ] P3 - Add `--output-dir` mode to emit one file per tag (better UX for large specs). (Impact 3/5, Effort 4/5, Strategic fit 3/5, Differentiation 3/5, Risk 3/5, Confidence 2/5)
- [ ] P3 - Add a minimal `--serve` mode for generated HTML (local static server + optional `--watch` rebuild). (Impact 3/5, Effort 4/5, Strategic fit 3/5, Differentiation 2/5, Risk 3/5, Confidence 2/5)
- [ ] P3 - Hosted docs preview. (Impact 4/5, Effort 5/5, Strategic fit 3/5, Differentiation 3/5, Risk 4/5, Confidence 1/5)

## Implemented
- [x] 2026-02-09 - Hardened CLI errors and made server selection discoverable via `--list-servers`.
  - Evidence: `src/devex_agent/cli.py`, `src/devex_agent/generator.py`, `tests/test_cli.py`, commit `a3ac5cd`, local `make check`, local `.venv/bin/devex-agent tests/fixtures/servers.yaml --list-servers`.
- [x] 2026-02-09 - Refreshed docs to reduce onboarding friction and reflect shipped CLI behavior.
  - Evidence: `README.md`, `docs/ROADMAP.md`, `docs/PROJECT.md`, `PLAN.md`, `AGENTS.md`.
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

## Notes
- This file is maintained by the autonomous clone loop.

### Auto-discovered Open Checklist Items (2026-02-09)
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] `make check`
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Update `docs/CHANGELOG.md`
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Tag release (SemVer)
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Create GitHub Release with notes
