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


class ItemView(ViewForAgents):
    """Parameterized page excluded from llms index by default."""

    template_name = "pages/item.html"
    include_in_llms = True

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        """Render item page for tests."""
        return self.render_to_response({"page_title": f"Item {slug}"})


class PrivateView(LoginRequiredMixin, ViewForAgents):
    """Auth-protected page auto-excluded from llms index."""

    template_name = "pages/private.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render private page for tests."""
        return self.render_to_response({"page_title": "Private"})


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("docs/", DocsView.as_view(), name="docs"),
    path("items/<slug:slug>/", ItemView.as_view(), name="item"),
    path("private/", PrivateView.as_view(), name="private"),
    path("", include("django_for_agents.urls")),
]
