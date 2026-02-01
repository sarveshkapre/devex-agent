from __future__ import annotations

import json
import re
import shlex
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

import httpx
import yaml


@dataclass
class RenderOptions:
    include_examples: bool = True
    include_curl: bool = True
    include_toc: bool = True
    group_by_tag: bool = True


def load_spec(source: str, timeout_s: float = 10.0) -> dict[str, Any]:
    raw = _load_raw(source, timeout_s)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("OpenAPI spec must be a JSON/YAML object at the top level.")
    return cast(dict[str, Any], data)


def _load_raw(source: str, timeout_s: float) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        resp = httpx.get(source, timeout=timeout_s, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    with open(source, encoding="utf-8") as handle:
        return handle.read()


def generate_markdown(spec: dict[str, Any], options: RenderOptions | None = None) -> str:
    opts = options or RenderOptions()
    info = spec.get("info", {})
    title = info.get("title", "API")
    version = info.get("version", "unknown")
    servers = spec.get("servers") or []
    base_url = servers[0].get("url") if servers else ""

    lines: list[str] = []
    lines.append(f"# {title} API Docs")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Version: {version}")
    if base_url:
        lines.append(f"- Base URL: {base_url}")
    lines.append("")
    lines.append("## Endpoints")
    lines.append("")

    operations = _collect_operations(spec)
    if opts.include_toc:
        _render_toc(lines, operations, group_by_tag=opts.group_by_tag)

    if opts.group_by_tag:
        for tag in _tag_order(operations):
            tag_anchor = f"tag-{_slugify(tag)}"
            lines.append(f'<a id="{tag_anchor}"></a>')
            lines.append(f"### {tag}")
            lines.append("")
            for op in operations:
                if op.tag != tag:
                    continue
                _render_operation(
                    lines,
                    op.path,
                    op.method,
                    op.path_item,
                    op.operation,
                    spec,
                    opts,
                    base_url=base_url,
                    heading_level=4,
                    op_anchor_id=op.anchor_id,
                )
    else:
        for op in operations:
            _render_operation(
                lines,
                op.path,
                op.method,
                op.path_item,
                op.operation,
                spec,
                opts,
                base_url=base_url,
                heading_level=3,
                op_anchor_id=op.anchor_id,
            )

    return "\n".join(lines).rstrip() + "\n"


def _sorted_methods(methods: Iterable[str]) -> list[str]:
    order = ["get", "post", "put", "patch", "delete", "options", "head"]
    return [m for m in order if m in methods]


def _render_operation(
    lines: list[str],
    path: str,
    method: str,
    path_item: dict[str, Any],
    operation: dict[str, Any],
    spec: dict[str, Any],
    opts: RenderOptions,
    *,
    base_url: str,
    heading_level: int,
    op_anchor_id: str,
) -> None:
    summary = operation.get("summary") or ""
    description = operation.get("description") or ""
    lines.append(f'<a id="{op_anchor_id}"></a>')
    lines.append(f'{"#" * heading_level} `{method.upper()} {path}`')
    lines.append("")
    if summary:
        lines.append(summary)
        lines.append("")
    if description:
        lines.append(description)
        lines.append("")

    params = _collect_parameters(path_item, operation, spec)
    if params:
        lines.append("#### Parameters")
        lines.append("")
        lines.append("| Name | In | Required | Type | Description |")
        lines.append("| --- | --- | --- | --- | --- |")
        for param in params:
            schema = param.get("schema", {})
            param_type = _schema_type(schema)
            required = "yes" if bool(param.get("required", False)) else "no"
            description_text = str(param.get("description", "")).replace("\n", " ")
            lines.append(
                f"| {param.get('name','')} | {param.get('in','')} | "
                f"{required} | {param_type} | {description_text} |"
            )
        lines.append("")

    request_body = operation.get("requestBody")
    request_content_type = ""
    request_example: Any | None = None
    if request_body:
        lines.append("#### Request Body")
        lines.append("")
        if opts.include_examples:
            request_example, request_content_type = _example_from_content(
                request_body.get("content", {}), spec
            )
            if request_example is not None:
                lines.append(f"Example ({request_content_type}):")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(request_example, indent=2))
                lines.append("```")
                lines.append("")
        else:
            request_content_type = _pick_content_type(request_body.get("content", {}))

    responses = operation.get("responses", {})
    accept_content_type = _pick_accept_content_type(responses)

    if opts.include_curl:
        curl = _curl_example(
            method=method,
            path=path,
            base_url=base_url,
            params=params,
            request_content_type=request_content_type,
            request_example=request_example,
            accept_content_type=accept_content_type,
            operation=operation,
            spec=spec,
            include_examples=opts.include_examples,
        )
        if curl:
            lines.append("#### Example curl")
            lines.append("")
            lines.append("```bash")
            lines.extend(curl.splitlines())
            lines.append("```")
            lines.append("")

    if responses:
        lines.append("#### Responses")
        lines.append("")
        for status in sorted(responses.keys()):
            response = responses[status]
            description = response.get("description", "")
            lines.append(f"- **{status}**: {description}")
            if opts.include_examples:
                example, content_type = _example_from_content(response.get("content", {}), spec)
                if example is not None:
                    lines.append("")
                    lines.append(f"  Example ({content_type}):")
                    lines.append("")
                    lines.append("  ```json")
                    lines.append("  " + json.dumps(example, indent=2).replace("\n", "\n  "))
                    lines.append("  ```")
        lines.append("")


def _collect_parameters(
    path_item: dict[str, Any], operation: dict[str, Any], spec: dict[str, Any]
) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []
    for param in path_item.get("parameters", []) or []:
        resolved = _resolve_ref(param, spec)
        params.append(resolved)
    for param in operation.get("parameters", []) or []:
        resolved = _resolve_ref(param, spec)
        params.append(resolved)
    return params


def _example_from_content(content: dict[str, Any], spec: dict[str, Any]) -> tuple[Any | None, str]:
    if not content:
        return None, ""
    content_type = "application/json" if "application/json" in content else next(iter(content))
    media = content.get(content_type, {})
    if "example" in media:
        return media["example"], content_type
    schema = media.get("schema", {})
    example = example_from_schema(schema, spec, depth=0)
    return example, content_type


def example_from_schema(schema: dict[str, Any], spec: dict[str, Any], depth: int) -> Any:
    if depth > 5:
        return None

    if "$ref" in schema:
        return example_from_schema(_resolve_ref(schema, spec), spec, depth + 1)

    if "example" in schema:
        return schema["example"]

    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    for key in ("oneOf", "anyOf", "allOf"):
        if key in schema and schema[key]:
            return example_from_schema(schema[key][0], spec, depth + 1)

    schema_type = schema.get("type")

    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        obj: dict[str, Any] = {}
        for name, subschema in properties.items():
            if required and name not in required:
                continue
            obj[name] = example_from_schema(subschema, spec, depth + 1)
        if not required:
            for name, subschema in list(properties.items())[:3]:
                obj[name] = example_from_schema(subschema, spec, depth + 1)
        return obj

    if schema_type == "array":
        item_schema = schema.get("items", {})
        item = example_from_schema(item_schema, spec, depth + 1)
        return [item] if item is not None else []

    if schema_type == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            return "2025-01-01T00:00:00Z"
        if fmt == "date":
            return "2025-01-01"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        return "string"

    if schema_type == "integer":
        return 0

    if schema_type == "number":
        return 0.0

    if schema_type == "boolean":
        return True

    return None


def _schema_type(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return str(schema["$ref"].split("/")[-1])
    schema_type = schema.get("type", "object")
    if isinstance(schema_type, list) and schema_type:
        return str(schema_type[0])
    return str(schema_type)


def _resolve_ref(node: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    ref = node.get("$ref")
    if not ref:
        return node
    if not ref.startswith("#/"):
        return node
    parts = ref[2:].split("/")
    current: Any = spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return node
    if isinstance(current, dict):
        return current
    return node


@dataclass(frozen=True)
class _OperationRef:
    path: str
    method: str
    path_item: dict[str, Any]
    operation: dict[str, Any]
    tag: str
    anchor_id: str


def _collect_operations(spec: dict[str, Any]) -> list[_OperationRef]:
    paths: dict[str, Any] = spec.get("paths", {})
    ops: list[_OperationRef] = []
    for path in sorted(paths.keys()):
        path_item = paths[path]
        for method in _sorted_methods(path_item.keys()):
            operation = path_item[method]
            tag = _primary_tag(operation)
            anchor_id = f"op-{_slugify(f'{method}-{path}')}"
            ops.append(
                _OperationRef(
                    path=path,
                    method=method,
                    path_item=path_item,
                    operation=operation,
                    tag=tag,
                    anchor_id=anchor_id,
                )
            )
    return ops


def _primary_tag(operation: dict[str, Any]) -> str:
    tags = operation.get("tags") or []
    if isinstance(tags, list) and tags and isinstance(tags[0], str) and tags[0].strip():
        return tags[0].strip()
    return "Untagged"


def _tag_order(operations: list[_OperationRef]) -> list[str]:
    tags = sorted({op.tag for op in operations if op.tag != "Untagged"})
    if any(op.tag == "Untagged" for op in operations):
        tags.append("Untagged")
    return tags


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "section"


def _render_toc(lines: list[str], operations: list[_OperationRef], *, group_by_tag: bool) -> None:
    if not operations:
        return

    lines.append("### Contents")
    lines.append("")
    if group_by_tag:
        for tag in _tag_order(operations):
            tag_anchor = f"tag-{_slugify(tag)}"
            lines.append(f"- [{tag}](#{tag_anchor})")
            for op in operations:
                if op.tag != tag:
                    continue
                label = f"{op.method.upper()} {op.path}"
                summary = op.operation.get("summary") or ""
                if summary:
                    label = f"{label} — {summary}"
                lines.append(f"  - [{label}](#{op.anchor_id})")
    else:
        for op in operations:
            label = f"{op.method.upper()} {op.path}"
            summary = op.operation.get("summary") or ""
            if summary:
                label = f"{label} — {summary}"
            lines.append(f"- [{label}](#{op.anchor_id})")
    lines.append("")


def _pick_content_type(content: dict[str, Any]) -> str:
    if not content:
        return ""
    if "application/json" in content:
        return "application/json"
    return next(iter(content))


def _pick_accept_content_type(responses: dict[str, Any]) -> str:
    for status in sorted(responses.keys()):
        response = responses[status]
        content = response.get("content", {}) or {}
        content_type = _pick_content_type(content)
        if content_type:
            return content_type
    return ""


def _rendered_url(base_url: str, path: str, query_params: dict[str, str]) -> str:
    base = base_url.strip()
    if not base:
        base = "<BASE_URL>"
    joined = base.rstrip("/") + path
    if query_params:
        joined = joined + "?" + urlencode(query_params)
    return joined


def _path_with_placeholders(path: str) -> str:
    pattern = r"\{([^}]+)\}"
    return re.sub(pattern, r"<\1>", path)


def _example_value_for_param(param: dict[str, Any], spec: dict[str, Any]) -> str:
    schema = param.get("schema", {}) or {}
    resolved_schema = _resolve_ref(schema, spec)
    example = example_from_schema(resolved_schema, spec, depth=0)
    if example is None:
        return "value"
    if isinstance(example, bool):
        return "true" if example else "false"
    if isinstance(example, (int, float, str)):
        return str(example)
    return json.dumps(example, separators=(",", ":"))


def _effective_security(operation: dict[str, Any], spec: dict[str, Any]) -> list[dict[str, Any]]:
    op_security = operation.get("security")
    if op_security is None:
        security = spec.get("security") or []
    else:
        security = op_security
    if not isinstance(security, list):
        return []
    return [cast(dict[str, Any], req) for req in security if isinstance(req, dict)]


def _security_headers_and_query(
    operation: dict[str, Any], spec: dict[str, Any]
) -> tuple[list[str], dict[str, str]]:
    requirements = _effective_security(operation, spec)
    if not requirements:
        return [], {}

    first_req = requirements[0]
    components = spec.get("components") or {}
    schemes = (components.get("securitySchemes") or {}) if isinstance(components, dict) else {}

    headers: list[str] = []
    query: dict[str, str] = {}
    for scheme_name in first_req.keys():
        scheme = schemes.get(scheme_name, {}) if isinstance(schemes, dict) else {}
        if not isinstance(scheme, dict):
            continue
        scheme_type = scheme.get("type")
        if scheme_type == "http":
            http_scheme = str(scheme.get("scheme") or "").lower()
            if http_scheme == "bearer":
                headers.append("Authorization: Bearer <token>")
            elif http_scheme == "basic":
                headers.append("Authorization: Basic <base64(username:password)>")
            else:
                headers.append("Authorization: <credentials>")
        elif scheme_type == "apiKey":
            name = str(scheme.get("name") or "X-API-Key")
            location = str(scheme.get("in") or "header")
            if location == "query":
                query[name] = "<api_key>"
            elif location == "header":
                headers.append(f"{name}: <api_key>")
        elif scheme_type in {"oauth2", "openIdConnect"}:
            headers.append("Authorization: Bearer <token>")
    return headers, query


def _format_curl(tokens: list[str]) -> str:
    quoted = [shlex.quote(t) for t in tokens]
    if len(quoted) <= 4:
        return " ".join(quoted)
    head = " ".join(quoted[:4])
    rest = quoted[4:]
    lines = [head + " \\"]
    for i in range(0, len(rest), 2):
        chunk = rest[i : i + 2]
        if i + 2 >= len(rest):
            lines.append("  " + " ".join(chunk))
        else:
            lines.append("  " + " ".join(chunk) + " \\")
    return "\n".join(lines)


def _curl_example(
    *,
    method: str,
    path: str,
    base_url: str,
    params: list[dict[str, Any]],
    request_content_type: str,
    request_example: Any | None,
    accept_content_type: str,
    operation: dict[str, Any],
    spec: dict[str, Any],
    include_examples: bool,
) -> str:
    path_rendered = _path_with_placeholders(path)

    query_params: dict[str, str] = {}
    required_query: list[dict[str, Any]] = []
    optional_query: list[dict[str, Any]] = []
    for param in params:
        if param.get("in") != "query":
            continue
        if bool(param.get("required", False)):
            required_query.append(param)
        else:
            optional_query.append(param)

    selected_query = required_query or optional_query[:2]
    for param in selected_query:
        name = str(param.get("name") or "")
        if not name:
            continue
        query_params[name] = _example_value_for_param(param, spec)

    security_headers, security_query = _security_headers_and_query(operation, spec)
    query_params = {**query_params, **security_query}

    url = _rendered_url(base_url, path_rendered, query_params)

    tokens: list[str] = ["curl", "-X", method.upper(), url]
    if accept_content_type:
        tokens.extend(["-H", f"Accept: {accept_content_type}"])
    for header in security_headers:
        tokens.extend(["-H", header])
    if request_content_type:
        tokens.extend(["-H", f"Content-Type: {request_content_type}"])

    if request_content_type and method.lower() in {"post", "put", "patch"}:
        if include_examples and request_example is not None:
            body = json.dumps(request_example, separators=(",", ":"), ensure_ascii=False)
            tokens.extend(["--data-raw", body])
        else:
            tokens.extend(["--data-raw", "<JSON_BODY>"])

    return _format_curl(tokens)
