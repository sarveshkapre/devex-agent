# PLAN

## Goal
Ship a CLI that turns OpenAPI specs into human-friendly API docs with request/response examples, and can re-generate when the spec changes.

## Stack
- Python 3.11
- Typer for CLI
- PyYAML + httpx for spec loading
- Ruff + mypy + pytest for quality

## Architecture
- `cli.py`: CLI entrypoint and watch loop
- `generator.py`: spec loading, example generation, markdown renderer
- `schemas.py`: (future) richer JSON Schema handling

## MVP checklist
- [x] CLI: `devex-agent generate <spec> --output <file>`
- [x] Supports JSON or YAML OpenAPI 3.x specs
- [x] Endpoint sections with parameters table
- [x] Request/response examples generated from schema
- [x] Watch mode for local files
- [x] Tests for example generation and markdown content

## Risks
- OpenAPI spec variations (oneOf/anyOf/allOf) may be lossy
- Example generation can be misleading for complex schemas
- Large specs may take longer to render (future pagination)

## Milestones
1. MVP CLI + docs + tests
2. Schema fidelity improvements (oneOf/allOf merge, formats)
3. Template theming and HTML export
