# DevEx Agent

Generate clean, always-current API documentation with examples from an OpenAPI spec.

## Why
Product teams ship APIs faster than docs can keep up. DevEx Agent turns any OpenAPI spec into readable docs with request/response examples, and can re-generate on every spec change.

## Features
- OpenAPI 3.0/3.1 JSON or YAML input
- Request/response examples generated from schemas
- Parameters table per endpoint
- `curl` examples per endpoint (base URL, params, request body, auth placeholders)
- Table of contents + endpoints grouped by tag
- Security summary per endpoint (based on OpenAPI `security`)
- `--strict` mode: fail generation on unresolved `$ref` and unsupported request/response content types
- `--lint` mode: fail-fast OpenAPI checks for unresolved `$ref`, duplicate `operationId`, duplicate parameters, and unused components
- Watch mode for local specs
- CLI-first, friendly output

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

devex-agent ./openapi.yaml --output ./API.md
```

## Base URL selection
By default, DevEx Agent uses the first OpenAPI `servers[0].url` as the Base URL for the overview and `curl` examples.

```bash
# List available servers (1-based indexes).
devex-agent ./openapi.yaml --list-servers

# Choose a different OpenAPI server (1-based index).
devex-agent ./openapi.yaml --server 2 --output ./API.md

# Or override explicitly (useful for staging/prod switches).
devex-agent ./openapi.yaml --base-url https://staging.api.example.com --output ./API.md
```

## Watch mode
```bash
devex-agent ./openapi.yaml --output ./API.md --watch
```

## HTML export
```bash
# `--format` is inferred from the output extension when omitted.
devex-agent ./openapi.yaml --output ./API.html
```
The HTML export includes endpoint navigation, filtering, and shareable deep links (filter state is kept
in the URL hash).

Preview locally:
```bash
devex-agent ./openapi.yaml --output ./API.html --serve
```

## Strict mode
By default, DevEx Agent is best-effort. Use `--strict` to fail fast when a spec contains
unresolved `$ref` or request/response bodies that DevEx Agent can't render.

Supported request/response content types for strict mode:
- `application/json`
- `application/*+json`

```bash
devex-agent ./openapi.yaml --strict --output ./API.md
```

## Lint mode
Run baseline spec lint checks and exit with code `2` when issues are found:

```bash
devex-agent ./openapi.yaml --lint
```

Checks:
- unresolved `$ref`
- duplicate `operationId`
- duplicate parameters in the same parameter list (`name` + `in`)
- unused components

For split specs, combine with local bundling:

```bash
devex-agent ./openapi.yaml --bundle --lint
```

## Multi-file specs (bundle external `$ref`)
Many real-world OpenAPI specs are split across multiple files using `$ref` (for example, schemas in
`./schemas.yaml` referenced from `./openapi.yaml`).

Use `--bundle` to inline external *local file* `$ref` before rendering (works for JSON or YAML
referenced files):

```bash
devex-agent ./openapi.yaml --bundle --output ./API.md
```

Notes:
- `--bundle` only supports local file `$ref` (not `http(s)://...` refs).
- Pair `--bundle` with `--strict` to fail fast if any referenced file or pointer can't be resolved.

## Docker
```bash
docker build -t devex-agent .
docker run --rm -v "$PWD:/work" devex-agent /work/openapi.yaml --output /work/API.md
```

## Output example
```bash
# Generated docs will include sections like:
# - Overview (title, version, base URL)
# - Endpoints with parameters
# - Example request/response payloads
```

## Status
MVP.

## License
MIT.
