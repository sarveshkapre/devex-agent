from pathlib import Path

from devex_agent.generator import RenderOptions, generate_markdown, load_spec


def test_generate_markdown_contains_endpoints() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "petstore.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    assert "# Petstore API Docs" in markdown
    assert "`GET /pets/{petId}`" in markdown
    assert "`POST /pets`" in markdown
    assert "Pet identifier" in markdown
    assert "Example (application/json):" in markdown
    assert "\"name\": \"string\"" in markdown
