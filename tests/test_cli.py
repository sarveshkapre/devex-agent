from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from typer.main import get_command

from devex_agent.cli import app


def test_format_is_inferred_from_output_extension_html() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "petstore.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            get_command(app),
            [str(spec_path), "--output", "out.html"],
        )
        assert result.exit_code == 0, result.output
        out = Path("out.html").read_text(encoding="utf-8")
        assert "<!doctype html>" in out


def test_format_is_inferred_from_output_extension_md() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "petstore.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            get_command(app),
            [str(spec_path), "--output", "out.md"],
        )
        assert result.exit_code == 0, result.output
        out = Path("out.md").read_text(encoding="utf-8")
        assert out.startswith("# Petstore API Docs")


def test_generate_prefix_is_accepted_for_compatibility() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "petstore.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            get_command(app),
            ["generate", str(spec_path), "--output", "out.md"],
        )
        assert result.exit_code == 0, result.output
        out = Path("out.md").read_text(encoding="utf-8")
        assert out.startswith("# Petstore API Docs")


def test_server_selection_option_affects_output() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "servers.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            get_command(app),
            [str(spec_path), "--server", "1", "--output", "out.md"],
        )
        assert result.exit_code == 0, result.output
        out = Path("out.md").read_text(encoding="utf-8")
        assert "- Base URL: https://us.api.example.com/v1" in out
