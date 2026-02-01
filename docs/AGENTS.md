# AGENTS

## Working agreement
- Keep changes small and shippable; update tests and docs together.
- Use `make check` as the quality gate before pushing.
- Prefer explicit, readable code over cleverness.
- Never commit secrets; use `.env` locally if needed.

## Commands
- Setup: `make setup`
- Dev: `make dev`
- Test: `make test`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Build: `make build`
- Full gate: `make check`

## Repo layout
- `src/devex_agent`: CLI and generation logic
- `tests`: pytest tests
- `docs/`: project documentation (except README)
