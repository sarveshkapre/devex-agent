# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration

## Candidate Features To Do
- [ ] P2 - Auto-detect output format from `--output` extension (e.g. `.md` vs `.html`) to reduce CLI friction. (Impact 3/5, Effort 1/5, Strategic fit 4/5, Differentiation 2/5, Risk 1/5, Confidence 4/5)
- [ ] P2 - Add multi-file spec merging support for split OpenAPI specs (roadmap later item). (Impact 4/5, Effort 4/5, Strategic fit 4/5, Differentiation 3/5, Risk 4/5, Confidence 2/5)
- [ ] P2 - Add spec diff mode to generate change-focused docs between two versions. (Impact 3/5, Effort 4/5, Strategic fit 3/5, Differentiation 3/5, Risk 3/5, Confidence 2/5)
- [ ] P2 - Add `--server` / `--base-url` selection to choose among OpenAPI `servers` (improves `curl` accuracy). (Impact 4/5, Effort 2/5, Strategic fit 4/5, Differentiation 2/5, Risk 2/5, Confidence 3/5)
- [ ] P3 - Add `--output-dir` mode to emit one file per tag (better UX for large specs). (Impact 3/5, Effort 4/5, Strategic fit 3/5, Differentiation 3/5, Risk 3/5, Confidence 2/5)
- [ ] P3 - Add a `--strict` mode to fail generation if `$ref` cannot be resolved or content types are unsupported. (Impact 2/5, Effort 3/5, Strategic fit 3/5, Differentiation 2/5, Risk 2/5, Confidence 3/5)
- [ ] P3 - Add optional non-`curl` code samples (HTTPie) for parity with common doc generators. (Impact 2/5, Effort 3/5, Strategic fit 3/5, Differentiation 2/5, Risk 2/5, Confidence 3/5)

## Implemented
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

## Insights
- CI failures across runs `21557668393` through `21557307241` shared the same root cause: `make check` assumed `.venv` activation.
- Typer is currently exposing single-command mode, so docs must use `devex-agent <spec> ...` instead of `devex-agent generate ...`.
- Regression coverage improved by adding fixtures for referenced request bodies and malformed path definitions.
- Market scan (bounded, 2026-02-09): baseline expectations for OpenAPI doc generators include static HTML export, theming, and built-in search or endpoint navigation; many tools also offer interactive "try it" consoles and spec bundling/linting.
- Market scan source: Redocly CLI `build-docs` (static HTML output, theming/search options) https://redocly.com/docs/cli/commands/build-docs
- Market scan source: Swagger UI (interactive browsing + "Try it out") https://github.com/swagger-api/swagger-ui
- Market scan source: Stoplight Elements (embeddable components, "Try It") https://stoplight.io/open-source/elements

## Notes
- This file is maintained by the autonomous clone loop.

### Auto-discovered Open Checklist Items (2026-02-09)
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] `make check`
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Update `docs/CHANGELOG.md`
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Tag release (SemVer)
- /Users/sarvesh/code/devex-agent/docs/RELEASE.md:- [ ] Create GitHub Release with notes
