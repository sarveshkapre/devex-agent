from __future__ import annotations

import html
import json
import re
import shlex
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

import httpx
import markdown  # type: ignore[import-untyped]
import yaml


@dataclass
class RenderOptions:
    include_examples: bool = True
    include_curl: bool = True
    include_toc: bool = True
    group_by_tag: bool = True
    strict: bool = False


def _expand_server_url(server: dict[str, Any]) -> str:
    url = str(server.get("url") or "")
    variables = server.get("variables") or {}
    if not isinstance(variables, dict):
        return url
    for name, meta in variables.items():
        if not isinstance(name, str) or not name:
            continue
        if not isinstance(meta, dict):
            continue
        value = meta.get("default")
        if value is None:
            enum = meta.get("enum")
            if isinstance(enum, list) and enum:
                value = enum[0]
        if value is None:
            continue
        url = url.replace("{" + name + "}", str(value))
    return url


def _select_base_url(
    spec: dict[str, Any],
    *,
    base_url_override: str | None = None,
    server: int | None = None,
) -> str:
    """
    Pick a base URL from OpenAPI `servers`.

    - `base_url_override` wins if provided.
    - `server` selects a 1-based server index (matching CLI UX).
    - Server URL variables are expanded using defaults (or first enum item).
    """
    if base_url_override:
        return base_url_override

    servers = spec.get("servers") or []
    if not isinstance(servers, list) or not servers:
        return ""

    idx = 0 if server is None else server - 1
    if idx < 0 or idx >= len(servers):
        raise ValueError(f"Invalid server index: {server} (expected 1..{len(servers)})")

    server_obj = servers[idx] or {}
    if not isinstance(server_obj, dict):
        return ""
    return _expand_server_url(server_obj)


def load_spec(source: str, timeout_s: float = 10.0) -> dict[str, Any]:
    raw = _load_raw(source, timeout_s)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            # Keep CLI output stable and avoid leaking a full traceback for common parse errors.
            raise ValueError(f"Failed to parse OpenAPI spec as JSON or YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("OpenAPI spec must be a JSON/YAML object at the top level.")
    return cast(dict[str, Any], data)


def _load_raw(source: str, timeout_s: float) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        try:
            resp = httpx.get(source, timeout=timeout_s, follow_redirects=True)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            raise ValueError(f"Failed to fetch OpenAPI spec from URL: {source}: {exc}") from exc
    with open(source, encoding="utf-8") as handle:
        return handle.read()


def list_servers(spec: dict[str, Any]) -> list[tuple[str, str | None]]:
    """
    Return a list of (expanded_url, description) for top-level OpenAPI `servers`.
    """
    servers = spec.get("servers") or []
    if not isinstance(servers, list):
        return []

    out: list[tuple[str, str | None]] = []
    for entry in servers:
        if not isinstance(entry, dict):
            continue
        url = _expand_server_url(entry)
        if not url:
            continue
        desc = entry.get("description")
        out.append((url, desc if isinstance(desc, str) and desc.strip() else None))
    return out


def _resolve_ref_target(spec: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    current: Any = spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _validate_refs_strict(spec: dict[str, Any]) -> None:
    """
    Validate that all `$ref` nodes in the spec are internal and resolvable.

    This is intentionally conservative: DevEx Agent currently doesn't support external `$ref`.
    """

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str):
                if not ref.startswith("#/"):
                    raise ValueError(f"Unsupported external $ref: {ref} at {path}")
                target = _resolve_ref_target(spec, ref)
                if not isinstance(target, dict):
                    raise ValueError(f"Unresolved $ref: {ref} at {path}")
            for k, v in node.items():
                key = k if isinstance(k, str) else "<non-string-key>"
                walk(v, f"{path}.{key}")
            return
        if isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(spec, "spec")


def _validate_content_types_strict(spec: dict[str, Any], operations: list[Any]) -> None:
    supported = "application/json, application/*+json"

    def validate_content(content: Any, *, context: str) -> None:
        if not isinstance(content, dict) or not content:
            return
        keys = [k for k in content.keys() if isinstance(k, str)]
        if any(_is_json_like_content_type(k) for k in keys):
            return
        rendered = ", ".join(keys) if keys else "<unknown>"
        raise ValueError(
            f"Unsupported content type(s) for {context}: {rendered} (supported: {supported})"
        )

    def resolve_ref_dict(node: Any, *, context: str) -> dict[str, Any]:
        if not isinstance(node, dict):
            return {}
        ref = node.get("$ref")
        if isinstance(ref, str):
            target = _resolve_ref_target(spec, ref)
            if isinstance(target, dict):
                return target
            raise ValueError(f"Unresolved $ref: {ref} at {context}")
        return node

    for op in operations:
        # `operations` is a list of _OperationRef. Keep this function loosely typed.
        path = getattr(op, "path", "<path>")
        method = getattr(op, "method", "<method>")
        operation = getattr(op, "operation", {}) or {}
        if not isinstance(operation, dict):
            continue

        rb = operation.get("requestBody")
        if rb is not None:
            resolved = resolve_ref_dict(rb, context=f"requestBody for {method.upper()} {path}")
            validate_content(
                resolved.get("content"),
                context=f"requestBody for {method.upper()} {path}",
            )

        responses = operation.get("responses") or {}
        if not isinstance(responses, dict):
            continue
        for status, resp in responses.items():
            resolved = resolve_ref_dict(
                resp,
                context=f"response {status} for {method.upper()} {path}",
            )
            validate_content(
                resolved.get("content"),
                context=f"response {status} for {method.upper()} {path}",
            )


def _validate_spec_strict(spec: dict[str, Any], operations: list[Any]) -> None:
    _validate_refs_strict(spec)
    _validate_content_types_strict(spec, operations)


def generate_markdown(
    spec: dict[str, Any],
    options: RenderOptions | None = None,
    *,
    base_url_override: str | None = None,
    server: int | None = None,
) -> str:
    opts = options or RenderOptions()
    info = spec.get("info", {})
    title = info.get("title", "API")
    version = info.get("version", "unknown")
    base_url = _select_base_url(spec, base_url_override=base_url_override, server=server)

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
    if opts.strict:
        _validate_spec_strict(spec, operations)
    tag_meta = _tag_metadata(spec)
    if opts.include_toc:
        _render_toc(lines, operations, group_by_tag=opts.group_by_tag, tag_meta=tag_meta)

    if opts.group_by_tag:
        for tag in _tag_order(operations, tag_meta):
            tag_anchor = f"tag-{_slugify(tag)}"
            lines.append(f'<a id="{tag_anchor}"></a>')
            lines.append(f"### {tag}")
            lines.append("")
            tag_description = tag_meta.get(tag)
            if tag_description:
                lines.append(tag_description)
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


def generate_html(
    spec: dict[str, Any],
    options: RenderOptions | None = None,
    *,
    base_url_override: str | None = None,
    server: int | None = None,
) -> str:
    """
    Generate a single self-contained HTML file with a minimal theme and client-side filtering.
    """
    opts = options or RenderOptions()

    info = spec.get("info", {})
    title = info.get("title", "API")
    version = info.get("version", "unknown")
    base_url = _select_base_url(spec, base_url_override=base_url_override, server=server)

    operations = _collect_operations(spec)
    tag_meta = _tag_metadata(spec)
    nav_html = _html_nav(operations, tag_meta=tag_meta, group_by_tag=opts.group_by_tag)

    # The HTML renderer owns navigation, so suppress the Markdown "Contents" section.
    md_opts = RenderOptions(
        include_examples=opts.include_examples,
        include_curl=opts.include_curl,
        include_toc=False,
        group_by_tag=opts.group_by_tag,
        strict=opts.strict,
    )
    md = generate_markdown(spec, md_opts, base_url_override=base_url_override, server=server)
    body = markdown.markdown(md, extensions=["fenced_code", "tables"])

    page_title = html.escape(f"{title} API Docs")
    subtitle_bits = [f"v{version}"]
    if base_url:
        subtitle_bits.append(base_url)
    subtitle = " · ".join(html.escape(x) for x in subtitle_bits if x)

    css = """
:root{
  --bg0:#fbfaf7;
  --bg1:#ffffff;
  --ink:#121212;
  --muted:#5b5b5b;
  --rule:#e7e3da;
  --accent:#0f5a4a;
  --accent2:#b71f2e;
  --codebg:#0f172a;
  --codeink:#e2e8f0;
  --shadow: 0 18px 45px rgba(0,0,0,.08);
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  color:var(--ink);
  background:
    radial-gradient(1200px 600px at 10% 0%, rgba(15,90,74,.08), transparent 55%),
    radial-gradient(900px 500px at 95% 15%, rgba(183,31,46,.08), transparent 50%),
    linear-gradient(180deg, var(--bg0), var(--bg1) 40%);
  font-family: ui-serif, "Iowan Old Style", "Palatino", "Palatino Linotype", serif;
}
a{color:var(--accent); text-decoration:none}
a:hover{text-decoration:underline}
.layout{
  display:grid;
  grid-template-columns: 320px 1fr;
  gap: 18px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 22px;
}
.sidebar{
  position: sticky;
  top: 18px;
  align-self: start;
  border:1px solid var(--rule);
  background: rgba(255,255,255,.78);
  backdrop-filter: blur(6px);
  border-radius: 14px;
  padding: 16px;
  box-shadow: var(--shadow);
}
.brand{
  font-weight: 700;
  letter-spacing: .2px;
  margin: 0 0 2px 0;
  font-size: 18px;
}
.subtitle{
  margin: 0 0 12px 0;
  color: var(--muted);
  font-size: 13px;
}
.search{
  width:100%;
  border:1px solid var(--rule);
  border-radius: 10px;
  padding: 10px 12px;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
  font-size: 14px;
  background: #fff;
}
.nav{
  margin-top: 12px;
  max-height: calc(100vh - 220px);
  overflow:auto;
  padding-right: 6px;
}
.tag{
  margin: 14px 0 8px 0;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .09em;
  color: var(--muted);
}
.nav a{
  display:block;
  padding: 7px 8px;
  border-radius: 10px;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
  font-size: 13px;
  color: var(--ink);
}
.nav a:hover{
  background: rgba(15,90,74,.08);
  text-decoration:none;
}
.main{
  border:1px solid var(--rule);
  background: rgba(255,255,255,.84);
  backdrop-filter: blur(6px);
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: var(--shadow);
  min-width: 0;
}
pre, code{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
}
pre{
  background: var(--codebg);
  color: var(--codeink);
  padding: 14px 16px;
  border-radius: 14px;
  overflow:auto;
}
code{background: rgba(15,23,42,.06); padding: 0 4px; border-radius: 6px}
pre code{background: transparent; padding: 0}
table{
  border-collapse: collapse;
  width:100%;
  overflow:hidden;
  border-radius: 12px;
  border:1px solid var(--rule);
}
th,td{padding:10px 10px; border-bottom:1px solid var(--rule); text-align:left; vertical-align:top}
th{
  background: rgba(15,90,74,.06);
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
}
h1,h2,h3,h4{scroll-margin-top: 16px}
@media (max-width: 980px){
  .layout{grid-template-columns: 1fr; padding: 14px}
  .sidebar{position: relative; top: 0}
  .nav{max-height: 340px}
}
"""

    js = """
(function(){
  var input = document.getElementById('search');
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav a[data-label]'));
  function norm(s){ return (s || '').toLowerCase(); }
  function apply(){
    var q = norm(input.value).trim();
    links.forEach(function(a){
      var label = norm(a.getAttribute('data-label'));
      a.style.display = (q === '' || label.indexOf(q) !== -1) ? '' : 'none';
    });
  }
  if (input){
    input.addEventListener('input', apply);
    apply();
  }
})();
"""

    out: list[str] = []
    out.append("<!doctype html>")
    out.append("<html lang=\"en\">")
    out.append("<head>")
    out.append("  <meta charset=\"utf-8\">")
    out.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    out.append(f"  <title>{page_title}</title>")
    out.append(f"  <style>{css}</style>")
    out.append("</head>")
    out.append("<body>")
    out.append("  <div class=\"layout\">")
    out.append("    <aside class=\"sidebar\">")
    out.append(f"      <div class=\"brand\">{page_title}</div>")
    out.append(f"      <div class=\"subtitle\">{subtitle}</div>")
    out.append(
        "      <input id=\"search\" class=\"search\" type=\"search\" "
        "placeholder=\"Filter endpoints...\" aria-label=\"Filter endpoints\">"
    )
    out.append("      <nav class=\"nav\">")
    out.append(nav_html)
    out.append("      </nav>")
    out.append("    </aside>")
    out.append("    <main class=\"main\">")
    out.append(body)
    out.append("    </main>")
    out.append("  </div>")
    out.append(f"  <script>{js}</script>")
    out.append("</body>")
    out.append("</html>")
    return "\n".join(out).rstrip() + "\n"


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

    _render_security(lines, operation, spec)

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
    resolved_request_body: dict[str, Any] = {}
    if isinstance(request_body, dict):
        resolved_request_body = _resolve_ref(request_body, spec)

    request_content_type = ""
    request_example: Any | None = None
    if resolved_request_body:
        lines.append("#### Request Body")
        lines.append("")
        if opts.include_examples:
            request_example, request_content_type = _example_from_content(
                cast(dict[str, Any], resolved_request_body.get("content", {})),
                spec,
            )
            if request_example is not None:
                lines.append(f"Example ({request_content_type}):")
                lines.append("")
                fence = _code_fence_language(request_content_type)
                lines.append(f"```{fence}")
                lines.append(_format_example(request_example, request_content_type))
                lines.append("```")
                lines.append("")
        else:
            request_content_type = _pick_content_type(
                cast(dict[str, Any], resolved_request_body.get("content", {}))
            )

    responses = operation.get("responses", {})
    if not isinstance(responses, dict):
        responses = {}
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
            response_obj = responses[status]
            if not isinstance(response_obj, dict):
                continue
            response = _resolve_ref(response_obj, spec)
            description = response.get("description", "")
            lines.append(f"- **{status}**: {description}")
            if opts.include_examples:
                example, content_type = _example_from_content(response.get("content", {}), spec)
                if example is not None:
                    lines.append("")
                    lines.append(f"  Example ({content_type}):")
                    lines.append("")
                    fence = _code_fence_language(content_type)
                    lines.append(f"  ```{fence}")
                    formatted = _format_example(example, content_type).replace("\n", "\n  ")
                    lines.append("  " + formatted)
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
    content_type = _pick_content_type(content)
    media = content.get(content_type, {})
    if not isinstance(media, dict):
        return None, content_type
    if "example" in media:
        return media["example"], content_type
    schema = media.get("schema", {}) or {}
    if not isinstance(schema, dict):
        return None, content_type
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

    if "allOf" in schema and schema["allOf"]:
        merged = _merge_allof_object_schema(schema["allOf"], spec)
        if merged is not None:
            return example_from_schema(merged, spec, depth + 1)

    for key in ("oneOf", "anyOf"):
        if key in schema and schema[key]:
            chosen, disc_prop, disc_value = _choose_variant_schema(schema, key=key, spec=spec)
            example = example_from_schema(chosen, spec, depth + 1)
            if disc_prop and isinstance(example, dict) and disc_prop not in example:
                # Ensure discriminator shows up even when it isn't marked required.
                example[disc_prop] = disc_value
            return example

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = _pick_non_null_type(schema_type)

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


def _pick_non_null_type(types: list[Any]) -> str | None:
    for t in types:
        if isinstance(t, str) and t != "null":
            return t
    # If everything is null/unknown, keep the first string entry.
    for t in types:
        if isinstance(t, str):
            return t
    return None


def _is_null_schema(schema: dict[str, Any]) -> bool:
    t = schema.get("type")
    if t == "null":
        return True
    if isinstance(t, list):
        # Treat union types that include non-null as non-null.
        return all(isinstance(x, str) and x == "null" for x in t)
    return False


def _choose_variant_schema(
    schema: dict[str, Any], *, key: str, spec: dict[str, Any]
) -> tuple[dict[str, Any], str | None, Any | None]:
    """
    Choose a stable variant for oneOf/anyOf example generation.

    Heuristics:
    - Prefer discriminator mapping when present.
    - Avoid explicit null schemas.
    - Prefer object-like schemas (more informative) and those that contain the discriminator
      property.
    """
    variants = schema.get(key) or []
    if not isinstance(variants, list) or not variants:
        return {}, None, None

    discriminator = schema.get("discriminator")
    disc_prop: str | None = None
    mapping: dict[str, Any] = {}
    if isinstance(discriminator, dict):
        prop = discriminator.get("propertyName")
        if isinstance(prop, str) and prop.strip():
            disc_prop = prop.strip()
        map_obj = discriminator.get("mapping") or {}
        if isinstance(map_obj, dict):
            mapping = map_obj

    # First try: pick the first mapped variant (stable) and propagate its discriminator value.
    if disc_prop and mapping:
        for disc_value, mapped_ref in mapping.items():
            if not isinstance(disc_value, str):
                continue
            if not isinstance(mapped_ref, str):
                continue
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                if variant.get("$ref") == mapped_ref:
                    return variant, disc_prop, disc_value

    def score_variant(variant: dict[str, Any]) -> int:
        resolved = _resolve_ref(variant, spec) if "$ref" in variant else variant
        if not isinstance(resolved, dict):
            return -10_000
        if _is_null_schema(resolved):
            return -10_000

        score = 0
        schema_type = resolved.get("type")
        if isinstance(schema_type, list):
            schema_type = _pick_non_null_type(schema_type)

        if schema_type == "object" or "properties" in resolved:
            score += 100
        props = resolved.get("properties") or {}
        if isinstance(props, dict):
            score += min(len(props), 10)
            if disc_prop and disc_prop in props:
                score += 50
        req = resolved.get("required") or []
        if isinstance(req, list):
            score += min(len([x for x in req if isinstance(x, str)]), 10) * 3
        return score

    best: dict[str, Any] | None = None
    best_score = -10_001
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        s = score_variant(variant)
        if s > best_score:
            best_score = s
            best = variant

    if best is not None:
        chosen = best
    else:
        chosen = cast(dict[str, Any], variants[0]) if isinstance(variants[0], dict) else {}

    # Determine a reasonable discriminator value (if requested).
    if disc_prop:
        resolved = _resolve_ref(chosen, spec) if "$ref" in chosen else chosen
        if isinstance(resolved, dict):
            properties = resolved.get("properties")
            disc_schema = properties.get(disc_prop) if isinstance(properties, dict) else None
            if isinstance(disc_schema, dict):
                enum = disc_schema.get("enum")
                if isinstance(enum, list) and enum:
                    return chosen, disc_prop, enum[0]

        if mapping:
            for disc_value in mapping.keys():
                if isinstance(disc_value, str):
                    return chosen, disc_prop, disc_value

        if isinstance(chosen, dict) and isinstance(chosen.get("$ref"), str):
            return chosen, disc_prop, chosen["$ref"].split("/")[-1]

        return chosen, disc_prop, "variant"

    return chosen, None, None


def _schema_type(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return str(schema["$ref"].split("/")[-1])
    schema_type = schema.get("type", "object")
    if isinstance(schema_type, list) and schema_type:
        picked = _pick_non_null_type(schema_type)
        return str(picked) if picked is not None else str(schema_type[0])
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


def _merge_allof_object_schema(all_of: Any, spec: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(all_of, list) or not all_of:
        return None

    merged_properties: dict[str, Any] = {}
    merged_required: set[str] = set()
    saw_object = False

    for item in all_of:
        if not isinstance(item, dict):
            return None
        resolved = _resolve_ref(item, spec) if "$ref" in item else item
        if not isinstance(resolved, dict):
            return None

        item_type = resolved.get("type")
        if item_type == "object" or "properties" in resolved:
            saw_object = True
        properties = resolved.get("properties", {}) or {}
        if isinstance(properties, dict):
            merged_properties.update(properties)
        required = resolved.get("required", []) or []
        if isinstance(required, list):
            merged_required.update(str(x) for x in required if isinstance(x, str))

    if not saw_object and not merged_properties:
        return None

    merged: dict[str, Any] = {"type": "object"}
    if merged_properties:
        merged["properties"] = merged_properties
    if merged_required:
        merged["required"] = sorted(merged_required)
    return merged


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
    if not isinstance(paths, dict):
        return []

    ops: list[_OperationRef] = []
    for path in sorted(paths.keys()):
        if not isinstance(path, str):
            continue
        path_item = paths[path]
        if not isinstance(path_item, dict):
            continue
        methods = [m for m in path_item.keys() if isinstance(m, str)]
        for method in _sorted_methods(methods):
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
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


def _tag_order(operations: list[_OperationRef], tag_meta: dict[str, str]) -> list[str]:
    present = {op.tag for op in operations}
    ordered: list[str] = []

    # Respect OpenAPI `tags` ordering where available.
    for tag in tag_meta.keys():
        if tag in present and tag != "Untagged":
            ordered.append(tag)

    # Append any tags not declared in `tags`.
    for tag in sorted(t for t in present if t not in tag_meta and t != "Untagged"):
        ordered.append(tag)

    if "Untagged" in present and "Untagged" not in ordered:
        ordered.append("Untagged")
    return ordered


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "section"


def _tag_metadata(spec: dict[str, Any]) -> dict[str, str]:
    tags = spec.get("tags") or []
    if not isinstance(tags, list):
        return {}
    meta: dict[str, str] = {}
    for tag in tags:
        if not isinstance(tag, dict):
            continue
        name = tag.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        description = tag.get("description")
        if isinstance(description, str) and description.strip():
            meta[name.strip()] = description.strip()
        else:
            meta[name.strip()] = ""
    return meta


def _render_toc(
    lines: list[str],
    operations: list[_OperationRef],
    *,
    group_by_tag: bool,
    tag_meta: dict[str, str],
) -> None:
    if not operations:
        return

    lines.append("### Contents")
    lines.append("")
    if group_by_tag:
        for tag in _tag_order(operations, tag_meta):
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


def _html_nav(
    operations: list[_OperationRef], *, tag_meta: dict[str, str], group_by_tag: bool
) -> str:
    if not operations:
        return ""

    out: list[str] = []
    if group_by_tag:
        for tag in _tag_order(operations, tag_meta):
            tag_anchor = f"tag-{_slugify(tag)}"
            tag_label = html.escape(tag)
            out.append(f"<div class=\"tag\"><a href=\"#{tag_anchor}\">{tag_label}</a></div>")
            for op in operations:
                if op.tag != tag:
                    continue
                label = f"{op.method.upper()} {op.path}"
                summary = op.operation.get("summary") or ""
                if summary:
                    label = f"{label} - {summary}"
                label_escaped = html.escape(label, quote=True)
                href = f"#{op.anchor_id}"
                out.append(f"<a href=\"{href}\" data-label=\"{label_escaped}\">{label_escaped}</a>")
    else:
        for op in operations:
            label = f"{op.method.upper()} {op.path}"
            summary = op.operation.get("summary") or ""
            if summary:
                label = f"{label} - {summary}"
            label_escaped = html.escape(label, quote=True)
            href = f"#{op.anchor_id}"
            out.append(f"<a href=\"{href}\" data-label=\"{label_escaped}\">{label_escaped}</a>")

    return "\n".join(out)


def _is_json_like_content_type(content_type: str) -> bool:
    ct = content_type.split(";", 1)[0].strip().lower()
    return ct == "application/json" or ct.endswith("+json")


def _pick_content_type(content: dict[str, Any]) -> str:
    """
    Prefer JSON-ish content types so examples are renderable and curl defaults are stable.
    """
    if not content:
        return ""
    if "application/json" in content:
        return "application/json"
    for ct in content.keys():
        if isinstance(ct, str) and _is_json_like_content_type(ct):
            return ct
    return next(iter(content))


def _pick_accept_content_type(responses: dict[str, Any]) -> str:
    """
    Choose a reasonable default for curl `Accept:` across responses.
    """
    candidates: list[str] = []
    for status in sorted(responses.keys()):
        response = responses[status]
        if not isinstance(response, dict):
            continue
        content = response.get("content", {}) or {}
        if not isinstance(content, dict) or not content:
            continue
        candidates.append(_pick_content_type(content))
    for ct in candidates:
        if ct == "application/json":
            return ct
    for ct in candidates:
        if _is_json_like_content_type(ct):
            return ct
    return candidates[0] if candidates else ""


def _code_fence_language(content_type: str) -> str:
    return "json" if (content_type and _is_json_like_content_type(content_type)) else "text"


def _format_example(example: Any, content_type: str) -> str:
    if _is_json_like_content_type(content_type):
        return json.dumps(example, indent=2)
    if isinstance(example, str):
        return example
    return json.dumps(example, indent=2)


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


def _render_security(lines: list[str], operation: dict[str, Any], spec: dict[str, Any]) -> None:
    requirements = _effective_security(operation, spec)
    if not requirements:
        # If the operation explicitly sets `security: []`, it means no auth required.
        if operation.get("security") == []:
            lines.append("#### Security")
            lines.append("")
            lines.append("No authentication required.")
            lines.append("")
        return

    components = spec.get("components") or {}
    schemes = (components.get("securitySchemes") or {}) if isinstance(components, dict) else {}

    lines.append("#### Security")
    lines.append("")
    lines.append("Authentication required (one of):")
    lines.append("")

    for idx, req in enumerate(requirements, start=1):
        parts: list[str] = []
        for scheme_name, scopes in req.items():
            detail = _describe_security_scheme(scheme_name, schemes)
            scope_text = ""
            if isinstance(scopes, list) and scopes:
                scope_text = f" (scopes: {', '.join(map(str, scopes))})"
            parts.append(f"{detail}{scope_text}")
        if not parts:
            continue
        prefix = f"{idx}. " if len(requirements) > 1 else "- "
        joiner = " + "  # AND within a single requirement object
        lines.append(prefix + joiner.join(parts))
    lines.append("")


def _describe_security_scheme(scheme_name: str, schemes: Any) -> str:
    scheme = schemes.get(scheme_name, {}) if isinstance(schemes, dict) else {}
    if not isinstance(scheme, dict):
        return scheme_name

    scheme_type = str(scheme.get("type") or "").strip() or "unknown"
    if scheme_type == "http":
        http_scheme = str(scheme.get("scheme") or "").strip() or "http"
        return f"{scheme_name} (http {http_scheme})"
    if scheme_type == "apiKey":
        name = str(scheme.get("name") or "X-API-Key")
        location = str(scheme.get("in") or "header")
        return f"{scheme_name} (apiKey in {location}: {name})"
    if scheme_type == "oauth2":
        return f"{scheme_name} (oauth2)"
    if scheme_type == "openIdConnect":
        return f"{scheme_name} (openIdConnect)"
    return f"{scheme_name} ({scheme_type})"


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
        json_like = _is_json_like_content_type(request_content_type)
        if include_examples and request_example is not None:
            if json_like:
                body = json.dumps(request_example, separators=(",", ":"), ensure_ascii=False)
            else:
                body = request_example if isinstance(request_example, str) else json.dumps(
                    request_example, separators=(",", ":"), ensure_ascii=False
                )
            tokens.extend(["--data-raw", body])
        else:
            tokens.extend(["--data-raw", "<JSON_BODY>" if json_like else "<REQUEST_BODY>"])

    return _format_curl(tokens)
