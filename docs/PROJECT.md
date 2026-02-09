# PROJECT

## Commands
- Setup: `make setup`
- Dev: `make dev`
- Test: `make test`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Build: `make build`
- Release: `make release`

## Local development
```bash
make setup
make dev
```

## Next 3 improvements
1. Spec diff mode for change-focused docs between two versions.
2. `--output-dir` mode to emit one file per tag (better UX for very large specs).
3. Performance: incremental/cached rendering for `--watch` on large specs.
