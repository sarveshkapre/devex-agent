# CHANGELOG

## Unreleased
- Add `--bundle` to inline external local file `$ref` so split OpenAPI specs can be rendered (optionally paired with `--strict`).
- Fix CI quality gate failure by making `make check` work both with and without a local `.venv`.
- Resolve referenced `requestBody` objects during rendering so generated request examples and `curl` payloads include schema-based bodies.
- Harden operation collection to ignore malformed path items instead of raising runtime errors.
- Add regression fixtures/tests for `requestBody` `$ref` handling and malformed path entries.
- Improve example generation for `oneOf`/`anyOf` with discriminator-aware variant selection and null-variant avoidance.
- Add HTML export via `--format html` with minimal theme and static endpoint filter/search.
- Improve HTML export UX: active nav highlight, shareable deep links (filter preserved in URL), and copy-link buttons.
- Add `--strict` mode to fail generation on unresolved `$ref` and unsupported request/response content types.
- Render non-JSON body examples with `text` fences and avoid emitting JSON payloads for non-JSON `curl` bodies.
- Infer output format from `--output` extension when `--format` is not provided.
- Accept `devex-agent generate <spec>` as a compatibility alias for single-command mode.
- Add Base URL controls: `--server` selection, `--base-url` override, and server-variable expansion for stable `curl` URLs.
- Align `devex_agent.__version__` with the packaged version.

## v0.1.6
- Improve watch mode UX (initial render, clearer status, graceful Ctrl+C).

## v0.1.5
- Respect OpenAPI top-level `tags` order and render tag descriptions.

## v0.1.4
- Improve example generation for `allOf` by merging object properties and required fields.

## v0.1.3
- Add per-endpoint security summaries (includes "no auth" for `security: []`).

## v0.1.2
- Add table of contents and group endpoints by tag (configurable via CLI).

## v0.1.1
- Add per-endpoint `curl` examples (base URL, params, request body).
- Include basic auth placeholders in `curl` examples for bearer and apiKey schemes.

## v0.1.0
- Initial MVP: generate Markdown API docs with examples from OpenAPI specs.
