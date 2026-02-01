# Update (2026-02-01)

## Shipped
- Added per-endpoint `curl` examples (base URL, params, request body).
- Added basic auth placeholders in `curl` examples for bearer/apiKey security schemes.
- Added tests covering `curl` output and security headers.

## Verify
- `make check`

## PR
- If `gh` is authenticated: `gh pr create --fill`
- Otherwise:
  - `git push -u origin <branch>`
  - Open a PR from that branch in GitHub UI

