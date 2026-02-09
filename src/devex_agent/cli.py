from __future__ import annotations

import time
from pathlib import Path

import typer

from devex_agent.generator import RenderOptions, generate_html, generate_markdown, load_spec

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
    watch: bool = typer.Option(False, "--watch", help="Watch local spec file for changes."),
    interval: float = typer.Option(1.0, "--interval", help="Watch poll interval in seconds."),
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

    options = RenderOptions(
        include_examples=not no_examples,
        include_curl=not no_curl,
        include_toc=not no_toc,
        group_by_tag=not no_group_by_tag,
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

    def render_once() -> None:
        spec_data = load_spec(spec_source)
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

    if not watch:
        render_once()
        return

    path = Path(spec_source)
    if not path.exists():
        typer.echo(f"File not found: {spec_source}")
        raise typer.Exit(code=1)

    last_mtime = path.stat().st_mtime
    typer.echo(f"Watching {spec_source} (poll every {interval:.1f}s). Press Ctrl+C to stop.")
    render_once()
    while True:
        try:
            current_mtime = path.stat().st_mtime
            if current_mtime > last_mtime:
                render_once()
                last_mtime = current_mtime
            time.sleep(interval)
        except KeyboardInterrupt:
            typer.echo("Stopped.")
            raise typer.Exit(code=0) from None
