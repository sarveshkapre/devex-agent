from pathlib import Path

import pytest

from devex_agent.generator import RenderOptions, generate_html, generate_markdown, load_spec


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


def test_request_body_refs_render_examples_and_curl_payloads() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "request_body_ref.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    assert "`POST /pets`" in markdown
    assert "#### Request Body" in markdown
    assert "\"name\": \"string\"" in markdown
    assert "\"age\": 0" in markdown
    assert "curl -X POST" in markdown
    assert "Content-Type: application/json" in markdown
    assert "--data-raw" in markdown


def test_operation_level_parameters_override_path_level_parameters() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "param_override.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    # OpenAPI operation-level params should override path-level params by (name, in).
    assert markdown.count("| lang | query |") == 1
    assert "Override language selector." in markdown
    assert "Default language selector." not in markdown
    assert "/pets?lang=fr" in markdown


def test_ignores_malformed_path_items_instead_of_crashing() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "malformed_paths.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(include_examples=False, include_curl=False))

    assert "`GET /valid`" in markdown
    assert "`GET /broken-operation`" not in markdown


def test_oneof_discriminator_prefers_mapped_variant_and_includes_discriminator() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "oneof_discriminator.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    assert "`POST /pet`" in markdown
    # Prefer the first discriminator mapping (cat) and include its required property.
    assert "\"huntingSkill\": \"string\"" in markdown
    assert "\"petType\": \"cat\"" in markdown


def test_oneof_avoids_null_variant_when_generating_examples() -> None:
    from devex_agent.generator import example_from_schema

    spec_path = Path(__file__).parent / "fixtures" / "oneof_discriminator.yaml"
    spec = load_spec(str(spec_path))
    schema = spec["components"]["schemas"]["PetOrNull"]
    example = example_from_schema(schema, spec, depth=0)

    assert isinstance(example, dict)
    assert example.get("petType") == "cat"
    assert "huntingSkill" in example


def test_generate_html_includes_search_and_endpoint_navigation() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "petstore.yaml"
    spec = load_spec(str(spec_path))
    page = generate_html(spec, RenderOptions())

    assert "<!doctype html>" in page
    assert "id=\"search\"" in page
    assert "Filter endpoints" in page
    assert "<h1>Petstore API Docs</h1>" in page
    assert "data-label=\"GET /pets/{petId}" in page
    assert "data-kind=\"op\"" in page
    assert "href=\"#op=" in page
    assert "URLSearchParams" in page
    assert ".copylink" in page


def test_server_selection_expands_server_variables_and_affects_curl_urls() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "servers.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(), server=1)

    assert "- Base URL: https://us.api.example.com/v1" in markdown
    assert "https://us.api.example.com/v1/pets" in markdown


def test_base_url_override_wins_over_spec_servers() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "servers.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(
        spec, RenderOptions(), base_url_override="https://override.example.test"
    )

    assert "- Base URL: https://override.example.test" in markdown
    assert "https://override.example.test/pets" in markdown


def test_strict_mode_fails_on_unresolved_ref() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "unresolved_ref.yaml"
    spec = load_spec(str(spec_path))
    with pytest.raises(ValueError) as exc:
        _ = generate_markdown(spec, RenderOptions(strict=True))
    assert "Unresolved $ref:" in str(exc.value)


def test_strict_mode_fails_on_unsupported_content_types() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "unsupported_content_type.yaml"
    spec = load_spec(str(spec_path))
    with pytest.raises(ValueError, match=r"Unsupported content type"):
        _ = generate_markdown(spec, RenderOptions(strict=True))


def test_non_strict_renders_text_plain_examples_as_text() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "unsupported_content_type.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions())

    assert "Example (text/plain):" in markdown
    assert "```text" in markdown


def test_ref_siblings_overlay_example_for_docs_rendering() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "ref_siblings.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(include_curl=False))

    assert "`GET /thing`" in markdown
    # The `example` sibling should override the referenced schema's generated example.
    assert "\"id\": \"override\"" in markdown


def test_escaped_json_pointer_refs_are_resolved_for_examples_and_strict_mode() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "escaped_ref.yaml"
    spec = load_spec(str(spec_path))

    markdown = generate_markdown(spec, RenderOptions(strict=True, include_curl=False))
    assert "\"id\": \"string\"" in markdown
    assert "\"state\": \"string\"" in markdown


def test_schema_examples_use_const_default_and_additional_properties() -> None:
    spec_path = Path(__file__).parent / "fixtures" / "schema_defaults.yaml"
    spec = load_spec(str(spec_path))
    markdown = generate_markdown(spec, RenderOptions(include_curl=False))

    assert "`GET /thing`" in markdown
    assert "\"status\": \"ok\"" in markdown
    assert "\"count\": 7" in markdown
    # additionalProperties map schema should render a representative key/value entry.
    assert "\"labels\": {" in markdown
    assert "\"key\": 0" in markdown
    # object default should be used as-is.
    assert "\"meta\": {" in markdown
    assert "\"source\": \"generated\"" in markdown
    assert "\"stable\": true" in markdown
