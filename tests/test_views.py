"""Tests for markdown negotiation behavior in ViewForAgents."""

from django.test import override_settings
from django.urls import reverse


def test_html_response_by_default(client):
    """Serve HTML when markdown is not requested."""
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


def test_markdown_response_when_accept_header_requests_it(client):
    """Serve markdown when Accept includes text/markdown."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")
    assert "Accept" in response.headers.get("Vary", "")


def test_markdown_links_use_absolute_urls(client):
    """Render absolute links in markdown templates via absolute_url filter."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")

    text = response.content.decode()
    assert "(http://testserver/docs/)" in text


@override_settings(DEBUG=True)
def test_markdown_can_be_forced_with_for_agents_query_param(client):
    """Force markdown output using ?for_agents=1 in debug mode."""
    response = client.get(reverse("home"), {"for_agents": "1"})

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")
