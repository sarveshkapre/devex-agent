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
python -m venv .venv
source .venv/bin/activate
pip install -e .

devex-agent generate ./openapi.yaml --output ./API.md
```

## Watch mode
```bash
devex-agent generate ./openapi.yaml --output ./API.md --watch
```

## Docker
```bash
docker build -t devex-agent .
docker run --rm -v "$PWD:/work" devex-agent generate /work/openapi.yaml --output /work/API.md
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
