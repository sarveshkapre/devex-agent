from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

import httpx
import yaml


@dataclass
class RenderOptions:
    include_examples: bool = True


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

    paths: dict[str, Any] = spec.get("paths", {})
    for path in sorted(paths.keys()):
        path_item = paths[path]
        for method in _sorted_methods(path_item.keys()):
            operation = path_item[method]
            _render_operation(lines, path, method, path_item, operation, spec, opts)

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
) -> None:
    summary = operation.get("summary") or ""
    description = operation.get("description") or ""
    lines.append(f"### `{method.upper()} {path}`")
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
            lines.append(
                f"| {param.get('name','')} | {param.get('in','')} | "
                f"{param.get('required', False)} | {param_type} | {param.get('description','')} |"
            )
        lines.append("")

    request_body = operation.get("requestBody")
    if request_body:
        lines.append("#### Request Body")
        lines.append("")
        if opts.include_examples:
            example, content_type = _example_from_content(request_body.get("content", {}), spec)
            if example is not None:
                lines.append(f"Example ({content_type}):")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(example, indent=2))
                lines.append("```")
                lines.append("")

    responses = operation.get("responses", {})
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
