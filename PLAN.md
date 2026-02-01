# DevEx Agent

One-line pitch: Turn any OpenAPI 3.x spec into clean, readable API docs (with examples) via a fast CLI.

## Features
- Generate Markdown docs from OpenAPI 3.0/3.1 (JSON/YAML)
- Endpoint sections with parameters table
- Request/response examples generated from schemas
- Watch mode to re-generate on spec changes

## Risks / Unknowns
- OpenAPI/schema edge-cases (deep `oneOf`/`allOf`, polymorphism, discriminators)
- Example fidelity vs. correctness for complex schemas
- Performance/UX on very large specs (pagination, grouping, search)

## Commands
- Setup: `make setup`
- Quality gate: `make check`
- Dev CLI: `make dev`

More details: `docs/PROJECT.md`

## Shipped (latest)
- v0.1.1: Add per-endpoint `curl` examples (incl. auth placeholders)
- v0.1.0: MVP Markdown generator + examples + watch mode

## Next
- Add auth/security summaries (bearer/apiKey) to docs + examples
- Group endpoints by tag + add a table of contents
- Consider HTML export with minimal theme + search
