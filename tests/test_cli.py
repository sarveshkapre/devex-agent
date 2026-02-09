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


def test_list_servers_prints_expanded_urls_and_exits() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "servers.yaml").resolve()
    runner = CliRunner()
    result = runner.invoke(get_command(app), [str(spec_path), "--list-servers"])
    assert result.exit_code == 0, result.output
    assert "Servers:" in result.output
    assert "1. https://us.api.example.com/v1" in result.output
    assert "2. https://eu.api.example.com/v1" in result.output


def test_missing_spec_file_exits_1_with_friendly_message() -> None:
    runner = CliRunner()
    result = runner.invoke(get_command(app), ["./does-not-exist.yaml", "--output", "out.md"])
    assert result.exit_code == 1, result.output
    assert "File not found:" in result.output


def test_invalid_yaml_exits_2_with_friendly_message() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("bad.yaml").write_text(
            "openapi: 3.0.0\ninfo: {title: x, version: 1.0\n",
            encoding="utf-8",
        )
        result = runner.invoke(get_command(app), ["bad.yaml", "--output", "out.md"])
        assert result.exit_code == 2, result.output
        assert "Failed to parse OpenAPI spec as JSON or YAML:" in result.output


def test_strict_mode_exits_2_on_unresolved_ref() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "unresolved_ref.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(get_command(app), [str(spec_path), "--strict", "--output", "out.md"])
        assert result.exit_code == 2, result.output
        assert "Unresolved $ref:" in result.output


def test_strict_mode_exits_2_on_unsupported_content_types() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "unsupported_content_type.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(get_command(app), [str(spec_path), "--strict", "--output", "out.md"])
        assert result.exit_code == 2, result.output
        assert "Unsupported content type(s)" in result.output


def test_strict_mode_exits_2_on_external_ref_without_bundle() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "multi_file_root.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(get_command(app), [str(spec_path), "--strict", "--output", "out.md"])
        assert result.exit_code == 2, result.output
        assert "Unsupported external $ref:" in result.output


def test_bundle_allows_external_ref_and_strict_passes() -> None:
    spec_path = (Path(__file__).parent / "fixtures" / "multi_file_root.yaml").resolve()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            get_command(app),
            [str(spec_path), "--bundle", "--strict", "--output", "out.md"],
        )
        assert result.exit_code == 0, result.output
        out = Path("out.md").read_text(encoding="utf-8")
        # Ensure the external schema reference was bundled and its internal refs were inlined.
        assert "\"pets\"" in out
        assert "\"kind\": \"dog\"" in out
        assert "\"id\": \"string\"" in out
