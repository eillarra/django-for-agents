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


def test_html_template_falls_back_to_markdown_conversion(client):
    """Convert rendered HTML to markdown when no matching .md template exists."""
    response = client.get(reverse("fallback"), HTTP_ACCEPT="text/markdown")

    text = response.content.decode()
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")
    assert "# Fallback" in text
    assert "Fallback body" in text


@override_settings(DEBUG=True)
def test_markdown_can_be_forced_with_for_agents_query_param(client):
    """Force markdown output using ?for_agents=1 in debug mode."""
    response = client.get(reverse("home"), {"for_agents": "1"})

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")


# --- Accept header parsing edge cases ---


def test_markdown_rejected_when_q_is_zero(client):
    """Do not serve markdown when the Accept header disables it with q=0."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown;q=0")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


def test_markdown_served_with_q_priority(client):
    """Serve markdown when listed alongside HTML with explicit q values."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/html;q=0.9, text/markdown;q=1.0")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")


def test_browser_accept_header_returns_html(client):
    """Serve HTML for a typical browser Accept header with */*;q=0.8."""
    response = client.get(
        reverse("home"),
        HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


def test_wildcard_only_accept_returns_html(client):
    """Serve HTML when Accept is */* and nothing else is specified."""
    response = client.get(reverse("home"), HTTP_ACCEPT="*/*")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


def test_text_wildcard_accept_returns_html(client):
    """Serve HTML when Accept is text/* and nothing else is specified."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/*")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


def test_empty_accept_header_returns_html(client):
    """Return HTML when Accept header is absent."""
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


# --- Token count headers ---


def test_markdown_response_includes_token_count_header(client):
    """Expose x-markdown-tokens to help agents estimate context size."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")

    assert "x-markdown-tokens" in response.headers
    tokens = int(response.headers["x-markdown-tokens"])
    assert tokens > 0


# --- Content-Signal header ---


def test_markdown_response_includes_default_content_signal(client):
    """Expose Content-Signal header with default permissive policy."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")

    assert "Content-Signal" in response.headers
    signal = response.headers["Content-Signal"]
    assert "ai-train=yes" in signal
    assert "search=yes" in signal
    assert "ai-input=yes" in signal


def test_html_response_does_not_include_content_signal(client):
    """Do not add Content-Signal to plain HTML responses."""
    response = client.get(reverse("home"))

    assert "Content-Signal" not in response.headers


@override_settings(FOR_AGENTS_CONTENT_SIGNAL="ai-train=no, search=yes, ai-input=no")
def test_content_signal_can_be_customized(client):
    """Render a custom Content-Signal header when configured."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")

    assert response.headers["Content-Signal"] == "ai-train=no, search=yes, ai-input=no"


# --- x-original-tokens on fallback path ---


def test_fallback_response_includes_original_token_count(client):
    """Expose x-original-tokens on the HTML fallback path."""
    response = client.get(reverse("fallback"), HTTP_ACCEPT="text/markdown")

    assert "x-original-tokens" in response.headers
    assert "x-markdown-tokens" in response.headers
    original = int(response.headers["x-original-tokens"])
    assert original > 0


# --- JSON-LD preservation ---


def test_fallback_preserves_json_ld(client):
    """Preserve JSON-LD blocks as a fenced json code block in fallback markdown."""
    response = client.get(reverse("jsonld"), HTTP_ACCEPT="text/markdown")

    text = response.content.decode()
    assert response.status_code == 200
    assert "```json" in text
    assert "@context" in text
    assert "schema.org" in text
    assert "WebPage" in text


# --- Frontmatter toggle ---


def test_frontmatter_can_be_disabled_per_view(client):
    """Omit YAML frontmatter when include_markdown_frontmatter is False."""
    from tests.urls import HomeView

    original = HomeView.include_markdown_frontmatter
    HomeView.include_markdown_frontmatter = False
    try:
        response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")
    finally:
        HomeView.include_markdown_frontmatter = original

    text = response.content.decode()
    assert not text.startswith("---")
    assert "# Home" in text


# --- Normalization ---


@override_settings(FOR_AGENTS_MAX_CONSECUTIVE_BLANK_LINES=0)
def test_markdown_normalization_collapses_blank_lines(client):
    """Collapse runs of blank lines according to the configured limit."""
    response = client.get(reverse("home"), HTTP_ACCEPT="text/markdown")

    text = response.content.decode()
    assert "\n\n\n" not in text


# --- agent_markdown context branch ---


def test_agent_markdown_context_is_used_when_no_template(client):
    """Fall back to the agent_markdown context value when no template exists."""
    from django.http import HttpRequest, HttpResponse

    from django_for_agents.views import ViewForAgents

    class AgentMarkdownView(ViewForAgents):
        template_name = ""

        def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
            context = {"page_title": "Agent", "agent_markdown": "# Agent-supplied markdown\nBody here."}
            return self.render_to_response(context)

    view = AgentMarkdownView()
    view.request = client.get("/", HTTP_ACCEPT="text/markdown").wsgi_request
    response = view.get(view.request)
    assert response.headers["Content-Type"].startswith("text/markdown")
    assert "Agent-supplied markdown" in response.content.decode()


# --- 501 when markdownify is missing and no .md template exists ---


def test_markdown_returns_501_when_markdownify_missing_and_no_md_template(client, monkeypatch):
    """Return 501 with an explanatory markdown body when markdown cannot be produced."""
    import builtins

    from django_for_agents import views

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "markdownify":
            raise ModuleNotFoundError("No module named 'markdownify'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    # Block only .md template lookups so the markdown fallback reaches
    # convert_html_to_markdown and hits the missing-dependency branch.
    original_render_to_string = views.render_to_string

    def fake_render_to_string(template_name, context=None, request=None, **kwargs):
        if isinstance(template_name, str) and template_name.endswith(".md"):
            raise views.TemplateDoesNotExist(template_name)
        return original_render_to_string(template_name, context=context, request=request, **kwargs)

    monkeypatch.setattr(views, "render_to_string", fake_render_to_string)

    response = client.get(reverse("fallback"), HTTP_ACCEPT="text/markdown")

    assert response.status_code == 501
    assert response.headers["Content-Type"].startswith("text/markdown")
    body = response.content.decode()
    assert "Markdown not available" in body
    assert "markdownify" in body
    assert "django-for-agents[markdown]" in body
