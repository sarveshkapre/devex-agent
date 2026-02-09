# ROADMAP

## Shipped
- HTML export with a minimal theme and endpoint filtering.
- Strict mode: `--strict` fails on unresolved `$ref` and unsupported request/response content types.
- Multi-file specs (local): `--bundle` inlines external file `$ref` so split OpenAPI specs can render.
- Base URL controls: `--server` selection, `--base-url` override, and server-variable expansion for stable `curl` examples.
- Reduce CLI friction: infer output format from `--output` extension (e.g. `.md` vs `.html`).
- Add `--list-servers` to make `--server` discoverable.
- Improve CLI errors (friendly messages + stable exit codes; fewer tracebacks).
- Auth/security summaries per endpoint.
- Improved schema example fidelity (including discriminator-aware `oneOf`/`anyOf` handling).

## Near-term
- Improve schema example fidelity on more real-world OpenAPI specs (continue adding fixtures/tests).

## Later
- Multi-file spec merging
- Diff mode for spec changes
- Hosted docs preview
