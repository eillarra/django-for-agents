"""Tests for automatic llms.txt endpoint generation."""

from django.urls import reverse


def test_llms_txt_endpoint_is_available(client):
    """Serve llms.txt from built-in plugin URL."""
    response = client.get(reverse("for_agents_llms_txt"))

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/plain")


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
