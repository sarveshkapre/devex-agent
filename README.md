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
