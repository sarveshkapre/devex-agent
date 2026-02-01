# CHANGELOG

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
