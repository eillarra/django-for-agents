"""``llms.txt`` rendering view for django-for-agents."""

from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_vary_headers
from django.views import View

from .discovery import LlmsEndpoint, collect_llms_endpoints


DEFAULT_INTRO = "Use `Accept: text/markdown` to fetch markdown responses when available."


def _setting(name: str, default: Any) -> Any:
    """Read plugin settings with FOR_AGENTS_ prefix.

    :param name: Setting key suffix.
    :param default: Fallback value.
    :returns: Setting value.
    """
    return getattr(settings, f"FOR_AGENTS_{name}", default)


def get_site_title() -> str:
    """Resolve the site title used by ``llms.txt`` header.

    Precedence: ``FOR_AGENTS_SITE_TITLE`` > current Django ``Site.name``
    (when ``django.contrib.sites`` is installed and configured) > ``"Site"``.

    :returns: Site title.
    """
    configured_title = _setting("SITE_TITLE", None)
    if configured_title:
        return str(configured_title)

    if "django.contrib.sites" in settings.INSTALLED_APPS:
        from django.contrib.sites.models import Site

        try:
            site = Site.objects.get_current()
        except Exception:
            pass
        else:
            if site.name:
                return str(site.name)

    return "Site"


class LlmsTxtView(View):
    """Serve an automatically generated ``llms.txt`` document."""

    def get_intro(self) -> str:
        """Return the introductory text shown below the site title.

        :returns: Intro line, empty string disables it.
        """
        return str(_setting("LLMS_INTRO", DEFAULT_INTRO))

    def get_format(self, request: HttpRequest) -> str:
        """Return response format requested via content negotiation.

        :param request: Incoming HTTP request.
        :returns: ``"text"`` (default) or ``"json"``.
        """
        accept = request.headers.get("Accept", "")
        for item in accept.split(","):
            media_range = item.split(";", maxsplit=1)[0].strip().lower()
            if media_range == "application/json":
                return "json"
            if media_range == "application/llms+json":
                return "json"
        return "text"

    def build_endpoints_payload(self, request: HttpRequest) -> list[dict[str, str | int]]:
        """Build the JSON-serializable representation of the endpoints.

        :param request: Incoming HTTP request.
        :returns: List of endpoint dictionaries with absolute URLs.
        """
        endpoints = collect_llms_endpoints()
        payload: list[dict[str, str | int]] = []
        for endpoint in endpoints:
            entry: dict[str, str | int] = {
                "title": endpoint.title,
                "kind": endpoint.kind,
                "url": request.build_absolute_uri(endpoint.path),
                "priority": endpoint.priority,
            }
            if endpoint.description:
                entry["description"] = endpoint.description
            payload.append(entry)
        return payload

    def render_text(self, request: HttpRequest) -> HttpResponse:
        """Render the plain-text ``llms.txt`` document.

        :param request: Incoming HTTP request.
        :returns: Plain-text HTTP response.
        """
        lines = [
            f"# {get_site_title()}",
            "",
        ]

        intro = self.get_intro()
        if intro:
            lines.append(intro)
            lines.append("")

        grouped: dict[str, list[LlmsEndpoint]] = {}
        for endpoint in collect_llms_endpoints():
            grouped.setdefault(endpoint.kind, []).append(endpoint)

        ordered_kinds = sorted(
            grouped.keys(),
            key=lambda kind: min(endpoint.priority for endpoint in grouped[kind]),
        )

        for kind in ordered_kinds:
            lines.append(f"## {kind}")
            lines.append("")

            for endpoint in sorted(
                grouped[kind], key=lambda endpoint: (endpoint.priority, endpoint.title, endpoint.path)
            ):
                absolute_url = request.build_absolute_uri(endpoint.path)
                lines.append(f"- {endpoint.title}")
                lines.append(f"  - url: {absolute_url}")
                if endpoint.description:
                    lines.append(f"  - description: {endpoint.description}")
                lines.append("")

        document = "\n".join(lines).rstrip() + "\n"
        response = HttpResponse(document, content_type="text/plain; charset=utf-8")
        patch_vary_headers(response, ("Accept",))
        return response

    def render_json(self, request: HttpRequest) -> HttpResponse:
        """Render the JSON ``llms.txt`` document.

        :param request: Incoming HTTP request.
        :returns: JSON HTTP response.
        """
        payload = {
            "title": get_site_title(),
            "endpoints": self.build_endpoints_payload(request),
        }
        intro = self.get_intro()
        if intro:
            payload["intro"] = intro

        document = json.dumps(payload, ensure_ascii=False, indent=2)
        response = HttpResponse(document, content_type="application/llms+json; charset=utf-8")
        patch_vary_headers(response, ("Accept",))
        return response

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Render ``llms.txt`` based on requested format.

        :param request: Incoming HTTP request.
        :returns: Plain-text or JSON ``llms.txt`` response.
        """
        if self.get_format(request) == "json":
            return self.render_json(request)
        return self.render_text(request)
