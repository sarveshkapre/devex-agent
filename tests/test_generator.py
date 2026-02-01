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
    assert "#### Example curl" in markdown
    assert "curl -X GET" in markdown
    assert "api.petstore.test/pets/<petId>" in markdown
    assert "curl -X POST" in markdown
    assert "--data-raw" in markdown
    assert "Example (application/json):" in markdown
    assert "\"name\": \"string\"" in markdown


def test_curl_examples_include_security_headers() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "secured.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    assert "`GET /me`" in markdown
    assert "curl -X GET" in markdown
    assert "api.secure.test/me" in markdown
    assert "Authorization: Bearer <token>" in markdown
