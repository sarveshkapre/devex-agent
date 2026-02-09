# ROADMAP

## Shipped
- HTML export with a minimal theme and endpoint filtering.
- Base URL controls: `--server` selection, `--base-url` override, and server-variable expansion for stable `curl` examples.
- Reduce CLI friction: infer output format from `--output` extension (e.g. `.md` vs `.html`).
- Add `--list-servers` to make `--server` discoverable.
- Improve CLI errors (friendly messages + stable exit codes; fewer tracebacks).
- Auth/security summaries per endpoint.
- Improved schema example fidelity (including discriminator-aware `oneOf`/`anyOf` handling).

## Near-term
- Add `--strict` mode for unresolved `$ref` / unsupported content types.
- Improve schema example fidelity on more real-world OpenAPI specs (continue adding fixtures/tests).

## Later
- Multi-file spec merging
- Diff mode for spec changes
- Hosted docs preview
