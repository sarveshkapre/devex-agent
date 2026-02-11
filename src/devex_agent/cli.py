from __future__ import annotations

import functools
import http.server
import threading
import time
from pathlib import Path

import typer

from devex_agent.generator import (
    RenderOptions,
    generate_html,
    generate_markdown,
    list_servers,
    load_spec,
    load_spec_bundled,
)

app = typer.Typer(add_completion=False, help="DevEx Agent: generate API docs from OpenAPI specs.")

_SPEC_ARG = typer.Argument(
    ...,
    help=(
        "Path or URL to OpenAPI spec (JSON/YAML). For compatibility, "
        "`devex-agent generate <spec>` is accepted."
    ),
)


@app.command()
def generate(
    spec: list[str] = _SPEC_ARG,
    output: str | None = typer.Option(None, "--output", "-o", help="Write output to file."),
    format: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: md or html. If omitted, inferred from --output extension.",
    ),
    server: int | None = typer.Option(
        None,
        "--server",
        help="Select OpenAPI server by 1-based index (affects Base URL and curl examples).",
    ),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        help="Override Base URL (affects Base URL and curl examples).",
    ),
    list_servers_only: bool = typer.Option(
        False,
        "--list-servers",
        help="Print available OpenAPI `servers` (expanded URLs) and exit.",
    ),
    watch: bool = typer.Option(False, "--watch", help="Watch local spec file for changes."),
    interval: float = typer.Option(1.0, "--interval", help="Watch poll interval in seconds."),
    serve: bool = typer.Option(
        False,
        "--serve",
        help="Serve generated HTML via a local static server (requires --output .html).",
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Host for --serve (default: 127.0.0.1)."),
    port: int = typer.Option(8000, "--port", help="Port for --serve (use 0 for random)."),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail generation on unresolved $ref and unsupported request/response content types.",
    ),
    bundle: bool = typer.Option(
        False,
        "--bundle",
        help="Inline external file $ref by bundling referenced local YAML/JSON files.",
    ),
    no_examples: bool = typer.Option(False, "--no-examples", help="Skip example generation."),
    no_curl: bool = typer.Option(False, "--no-curl", help="Skip generating curl examples."),
    no_toc: bool = typer.Option(False, "--no-toc", help="Skip generating a table of contents."),
    no_group_by_tag: bool = typer.Option(
        False, "--no-group-by-tag", help="Don't group endpoints by tag."
    ),
) -> None:
    """Generate API docs (Markdown or HTML) from an OpenAPI spec."""
    spec_source = spec[0]
    if spec_source == "generate":
        if len(spec) < 2:
            typer.echo("Missing spec path after 'generate'.")
            raise typer.Exit(code=2)
        if len(spec) > 2:
            typer.echo(f"Unexpected extra arguments: {' '.join(spec[2:])}")
            raise typer.Exit(code=2)
        spec_source = spec[1]
    elif len(spec) > 1:
        typer.echo(f"Unexpected extra arguments: {' '.join(spec[1:])}")
        raise typer.Exit(code=2)

    if watch and (spec_source.startswith("http://") or spec_source.startswith("https://")):
        typer.echo("Watch mode only supports local files.")
        raise typer.Exit(code=2)
    if watch and interval <= 0:
        typer.echo("--interval must be > 0.")
        raise typer.Exit(code=2)

    options = RenderOptions(
        include_examples=not no_examples,
        include_curl=not no_curl,
        include_toc=not no_toc,
        group_by_tag=not no_group_by_tag,
        strict=strict,
    )

    fmt_in = (format or "").strip().lower()
    if not fmt_in and output:
        suffix = Path(output).suffix.lower()
        if suffix in {".html", ".htm"}:
            fmt_in = "html"
        elif suffix in {".md", ".markdown"}:
            fmt_in = "md"

    fmt = fmt_in or "md"
    if fmt not in {"md", "markdown", "html"}:
        typer.echo(f"Unsupported --format: {format} (expected: md|html)")
        raise typer.Exit(code=2)

    if serve:
        if not output:
            typer.echo("--serve requires --output to be set (an .html file).")
            raise typer.Exit(code=2)
        if fmt != "html":
            typer.echo("--serve only supports HTML output (use --output *.html or --format html).")
            raise typer.Exit(code=2)
        suffix = Path(output).suffix.lower()
        if suffix not in {".html", ".htm"}:
            typer.echo("--serve requires an .html output file (use --output *.html).")
            raise typer.Exit(code=2)
        if port < 0 or port > 65535:
            typer.echo("--port must be in range 0..65535.")
            raise typer.Exit(code=2)

    class _QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

    def _make_server(directory: Path) -> http.server.ThreadingHTTPServer:
        handler = functools.partial(_QuietHandler, directory=str(directory))
        return http.server.ThreadingHTTPServer((host, port), handler)

    def render_once() -> None:
        try:
            spec_data = load_spec_bundled(spec_source) if bundle else load_spec(spec_source)
        except FileNotFoundError:
            typer.echo(f"File not found: {spec_source}")
            raise typer.Exit(code=1) from None
        except OSError as exc:
            typer.echo(f"Failed to read file: {spec_source}: {exc}")
            raise typer.Exit(code=1) from exc
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=2) from exc

        if list_servers_only:
            servers = list_servers(spec_data)
            if not servers:
                typer.echo("No OpenAPI servers found (spec has no top-level `servers`).")
                raise typer.Exit(code=0)
            typer.echo("Servers:")
            for i, (url, desc) in enumerate(servers, start=1):
                suffix = f" - {desc}" if desc else ""
                typer.echo(f"{i}. {url}{suffix}")
            raise typer.Exit(code=0)

        try:
            if fmt in {"html"}:
                rendered = generate_html(
                    spec_data, options, base_url_override=base_url, server=server
                )
            else:
                rendered = generate_markdown(
                    spec_data, options, base_url_override=base_url, server=server
                )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=2) from exc
        if output:
            Path(output).write_text(rendered, encoding="utf-8")
            typer.echo(f"Wrote {output}")
        else:
            typer.echo(rendered)

    server_obj: http.server.ThreadingHTTPServer | None = None

    if not watch:
        render_once()
        if not serve:
            return
        if output is None:
            typer.echo("--serve requires --output to be set (an .html file).")
            raise typer.Exit(code=2)
        out_path = Path(output).resolve()
        server_obj = _make_server(out_path.parent)
        actual_port = int(server_obj.server_address[1])
        typer.echo(f"Serving http://{host}:{actual_port}/{out_path.name} (Ctrl+C to stop)")
        try:
            server_obj.serve_forever()
        except KeyboardInterrupt:
            server_obj.shutdown()
        return

    path = Path(spec_source)
    if not path.exists():
        typer.echo(f"File not found: {spec_source}")
        raise typer.Exit(code=1)

    last_mtime = path.stat().st_mtime
    typer.echo(f"Watching {spec_source} (poll every {interval:.1f}s). Press Ctrl+C to stop.")
    render_once()
    if serve:
        if output is None:
            typer.echo("--serve requires --output to be set (an .html file).")
            raise typer.Exit(code=2)
        out_path = Path(output).resolve()
        server_obj = _make_server(out_path.parent)
        thread = threading.Thread(target=server_obj.serve_forever, daemon=True)
        thread.start()
        actual_port = int(server_obj.server_address[1])
        typer.echo(f"Serving http://{host}:{actual_port}/{out_path.name}")
    while True:
        try:
            current_mtime = path.stat().st_mtime
            if current_mtime > last_mtime:
                render_once()
                last_mtime = current_mtime
            time.sleep(interval)
        except KeyboardInterrupt:
            if server_obj is not None:
                server_obj.shutdown()
            typer.echo("Stopped.")
            raise typer.Exit(code=0) from None
