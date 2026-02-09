# ROADMAP

## Shipped
- HTML export with a minimal theme and endpoint filtering.
- Auth/security summaries per endpoint.
- Improved schema example fidelity (including discriminator-aware `oneOf`/`anyOf` handling).

## Near-term
- Base URL controls: `--server` selection, `--base-url` override, and server-variable expansion for stable `curl` examples.
- Reduce CLI friction: infer output format from `--output` extension (e.g. `.md` vs `.html`).
- Improve schema example fidelity on more real-world OpenAPI specs (continue adding fixtures/tests).

## Later
- Multi-file spec merging
- Diff mode for spec changes
- Hosted docs preview
