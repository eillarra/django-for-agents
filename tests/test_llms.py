"""Tests for automatic llms.txt endpoint generation."""

import json

from django.test import override_settings
from django.urls import reverse


def test_llms_txt_endpoint_is_available(client):
    """Serve llms.txt from built-in plugin URL."""
    response = client.get(reverse("for_agents_llms_txt"))

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/plain")


def test_llms_txt_uses_configured_site_title_and_neutral_intro(client):
    """Render configured site title and framework-neutral intro copy."""
    response = client.get(reverse("for_agents_llms_txt"))

    text = response.content.decode()
    assert text.startswith("# django-for-agents test site\n")
    assert "Agent-ready endpoint index discovered" not in text
    assert "Use `Accept: text/markdown`" in text


@override_settings(FOR_AGENTS_SITE_TITLE=None)
def test_llms_txt_falls_back_to_generic_site_title(client):
    """Use a neutral generic title when no site title is configured."""
    response = client.get(reverse("for_agents_llms_txt"))

    text = response.content.decode()
    assert text.startswith("# Site\n")


@override_settings(FOR_AGENTS_LLMS_INTRO="")
def test_llms_txt_intro_can_be_disabled(client):
    """Omit the intro line when configured to empty string."""
    response = client.get(reverse("for_agents_llms_txt"))

    text = response.content.decode()
    assert "Use `Accept: text/markdown`" not in text


@override_settings(FOR_AGENTS_LLMS_INTRO="Custom intro for agents.")
def test_llms_txt_intro_can_be_customized(client):
    """Render a custom intro line when configured."""
    response = client.get(reverse("for_agents_llms_txt"))

    text = response.content.decode()
    assert "Custom intro for agents." in text


def test_llms_txt_vary_accept_header_is_set(client):
    """Vary on Accept so caches distinguish text and JSON variants."""
    response = client.get(reverse("for_agents_llms_txt"))

    assert "Accept" in response.headers.get("Vary", "")


def test_llms_txt_lists_public_agent_views(client):
    """Include home and docs entries from ViewForAgents subclasses."""
    response = client.get(reverse("for_agents_llms_txt"))

    text = response.content.decode()
    assert "## homepage" in text
    assert "## docs" in text
    assert "http://testserver/" in text
    assert "http://testserver/docs/" in text


def test_llms_txt_excludes_private_and_parameterized_routes(client):
    """Exclude auth-gated and parameterized routes by default."""
    response = client.get(reverse("for_agents_llms_txt"))

    text = response.content.decode()
    assert "http://testserver/private/" not in text
    assert "http://testserver/items/{slug}/" not in text


def test_llms_txt_json_format(client):
    """Serve a JSON document when application/llms+json is accepted."""
    response = client.get(
        reverse("for_agents_llms_txt"),
        HTTP_ACCEPT="application/llms+json",
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/llms+json")
    assert "Accept" in response.headers.get("Vary", "")

    payload = json.loads(response.content)
    assert payload["title"] == "django-for-agents test site"
    titles = {entry["title"] for entry in payload["endpoints"]}
    assert {"HomeView", "DocsView"} <= titles


def test_llms_txt_json_format_via_application_json(client):
    """Serve JSON when application/json is accepted."""
    response = client.get(
        reverse("for_agents_llms_txt"),
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/llms+json")
