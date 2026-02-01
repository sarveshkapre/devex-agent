from pathlib import Path

from devex_agent.generator import RenderOptions, generate_markdown, load_spec


def test_render_options_are_constructible() -> None:
    _ = RenderOptions()


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


def test_groups_endpoints_by_tag_and_renders_toc() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "tagged.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    assert "### Contents" in markdown
    assert "- [Pets](#tag-pets)" in markdown
    assert "- [Users](#tag-users)" in markdown
    assert "### Pets" in markdown
    assert "### Users" in markdown
    assert "`GET /pets`" in markdown
    assert "`GET /users`" in markdown


def test_respects_top_level_tag_order_and_renders_tag_descriptions() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "tag_order.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(include_curl=False))

    users_idx = markdown.find("### Users")
    pets_idx = markdown.find("### Pets")
    assert users_idx != -1
    assert pets_idx != -1
    assert users_idx < pets_idx
    assert "User operations." in markdown
    assert "Pet operations." in markdown


def test_security_summary_renders_for_required_and_public_endpoints() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "security.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(include_curl=False))

    assert "`GET /private`" in markdown
    assert "#### Security" in markdown
    assert "bearerAuth (http bearer)" in markdown
    assert "`GET /public`" in markdown
    assert "No authentication required." in markdown


def test_allof_examples_merge_object_fields() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "allof.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(include_curl=False))

    assert "`GET /thing`" in markdown
    assert "\"id\": \"string\"" in markdown
    assert "\"name\": \"string\"" in markdown
    assert "\"createdAt\": \"2025-01-01T00:00:00Z\"" in markdown
