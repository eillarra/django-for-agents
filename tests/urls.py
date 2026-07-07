"""URL configuration for django-for-agents tests."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.urls import include, path

from django_for_agents.views import ViewForAgents


class HomeView(ViewForAgents):
    """Public homepage for testing markdown negotiation."""

    template_name = "pages/home.html"
    include_in_llms = True
    llms_kind = "homepage"
    llms_description = "Main entry page."
    llms_priority = 10
    enable_dev_toggle = True

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render home page for tests."""
        context = {
            "page_title": "Home",
            "meta_description": "Home page",
            "body": "Hello world",
        }
        return self.render_to_response(context)


class DocsView(ViewForAgents):
    """Public docs page for testing markdown links."""

    template_name = "pages/docs.html"
    include_in_llms = True
    llms_kind = "docs"
    llms_description = "Documentation pages."
    llms_priority = 20

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render docs page for tests."""
        return self.render_to_response({"page_title": "Docs", "body": "Docs body"})


class HtmlFallbackView(ViewForAgents):
    """Page that relies on HTML-to-Markdown fallback when no .md template exists."""

    template_name = "pages/fallback.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render HTML-only page for fallback tests."""
        return self.render_to_response({"page_title": "Fallback", "body": "Fallback body"})


class ItemView(ViewForAgents):
    """Parameterized page excluded from llms index by default."""

    template_name = "pages/item.html"
    include_in_llms = True

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        """Render item page for tests."""
        return self.render_to_response({"page_title": f"Item {slug}"})


class JsonLdFallbackView(ViewForAgents):
    """Page that relies on the HTML fallback and embeds JSON-LD structured data."""

    template_name = "pages/with_jsonld.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render a page with JSON-LD for fallback conversion tests."""
        return self.render_to_response({"page_title": "JSON-LD Page", "body": "Body with structured data."})


class PrivateView(LoginRequiredMixin, ViewForAgents):
    """Auth-protected page auto-excluded from llms index."""

    template_name = "pages/private.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render private page for tests."""
        return self.render_to_response({"page_title": "Private"})


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("docs/", DocsView.as_view(), name="docs"),
    path("fallback/", HtmlFallbackView.as_view(), name="fallback"),
    path("jsonld/", JsonLdFallbackView.as_view(), name="jsonld"),
    path("items/<slug:slug>/", ItemView.as_view(), name="item"),
    path("private/", PrivateView.as_view(), name="private"),
    path("", include("django_for_agents.urls")),
]
