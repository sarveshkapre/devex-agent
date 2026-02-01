from __future__ import annotations

import time
from pathlib import Path

import typer

from devex_agent.generator import RenderOptions, generate_markdown, load_spec

app = typer.Typer(add_completion=False, help="DevEx Agent: generate API docs from OpenAPI specs.")


@app.command()
def generate(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec (JSON/YAML)."),
    output: str | None = typer.Option(None, "--output", "-o", help="Write output to file."),
    watch: bool = typer.Option(False, "--watch", help="Watch local spec file for changes."),
    interval: float = typer.Option(1.0, "--interval", help="Watch poll interval in seconds."),
    no_examples: bool = typer.Option(False, "--no-examples", help="Skip example generation."),
    no_curl: bool = typer.Option(False, "--no-curl", help="Skip generating curl examples."),
) -> None:
    """Generate Markdown API docs from an OpenAPI spec."""
    if watch and (spec.startswith("http://") or spec.startswith("https://")):
        typer.echo("Watch mode only supports local files.")
        raise typer.Exit(code=2)

    options = RenderOptions(include_examples=not no_examples, include_curl=not no_curl)

    def render_once() -> None:
        spec_data = load_spec(spec)
        markdown = generate_markdown(spec_data, options)
        if output:
            Path(output).write_text(markdown, encoding="utf-8")
        else:
            typer.echo(markdown)

    if not watch:
        render_once()
        return

    path = Path(spec)
    if not path.exists():
        typer.echo(f"File not found: {spec}")
        raise typer.Exit(code=1)

    last_mtime = 0.0
    typer.echo(f"Watching {spec}...")
    while True:
        current_mtime = path.stat().st_mtime
        if current_mtime > last_mtime:
            render_once()
            last_mtime = current_mtime
        time.sleep(interval)
