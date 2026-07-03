"""Automatic llms.txt registry generation for ViewForAgents routes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, URLResolver, get_resolver
from django.views import View

from .views import ViewForAgents


def _setting(name: str, default: Any) -> Any:
    """Read plugin settings with FOR_AGENTS_ prefix.

    :param name: Setting key suffix.
    :param default: Fallback value.
    :returns: Setting value.
    """
    return getattr(settings, f"FOR_AGENTS_{name}", default)


@dataclass(frozen=True)
class LlmsEndpoint:
    """Serializable llms.txt endpoint entry."""

    path: str
    name: str
    title: str
    kind: str
    description: str
    priority: int


def _join_route(prefix: str, route: str) -> str:
    """Join URL resolver prefixes and route fragments.

    :param prefix: Accumulated route prefix.
    :param route: Current route segment.
    :returns: Joined route without leading slash.
    """
    return f"{prefix}{route}"


def _normalize_parameterized_route(route: str) -> str:
    """Convert Django converter segments to readable placeholders.

    :param route: Raw Django route string.
    :returns: Human-readable route template.
    """

    def _replace(match: re.Match[str]) -> str:
        parameter = match.group(2)
        return "{" + parameter + "}"

    return re.sub(r"<(?:(\w+):)?(\w+)>", _replace, route)


def _iter_agent_ready_patterns(patterns: list[URLPattern | URLResolver], prefix: str = "") -> list[LlmsEndpoint]:
    """Recursively discover ViewForAgents URL patterns.

    :param patterns: URL pattern list from a resolver.
    :param prefix: Route prefix inherited from parent resolvers.
    :returns: Discovered endpoint entries.
    """
    endpoints: list[LlmsEndpoint] = []

    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            nested_prefix = _join_route(prefix, str(pattern.pattern))
            endpoints.extend(_iter_agent_ready_patterns(pattern.url_patterns, prefix=nested_prefix))
            continue

        callback = pattern.callback
        view_class = getattr(callback, "view_class", None)
        if not isinstance(view_class, type):
            continue
        if not issubclass(view_class, ViewForAgents):
            continue
        if not getattr(view_class, "agent_ready_enabled", True):
            continue

        include_in_llms = getattr(view_class, "include_in_llms", None)
        if include_in_llms is False:
            continue
        if include_in_llms is None and issubclass(view_class, AccessMixin):
            continue

        route = _join_route(prefix, str(pattern.pattern))
        contains_parameters = "<" in route and ">" in route
        include_parameterized = getattr(view_class, "llms_include_parameterized_routes", False)
        if contains_parameters and not include_parameterized:
            continue

        if contains_parameters:
            route = _normalize_parameterized_route(route)

        normalized_route = "/" + route.lstrip("/")
        name = pattern.name or normalized_route
        title = (
            getattr(view_class, "llms_title", None) or getattr(view_class, "page_title", None) or view_class.__name__
        )
        kind = getattr(view_class, "llms_kind", "general")
        description = getattr(view_class, "llms_description", "")
        priority = int(getattr(view_class, "llms_priority", 100))

        endpoints.append(
            LlmsEndpoint(
                path=normalized_route,
                name=str(name),
                title=str(title),
                kind=str(kind),
                description=str(description),
                priority=priority,
            )
        )

    return endpoints


def collect_llms_endpoints() -> list[LlmsEndpoint]:
    """Collect and sort llms.txt endpoint entries.

    :returns: Sorted endpoint list.
    """
    endpoints = _iter_agent_ready_patterns(get_resolver().url_patterns)
    return sorted(endpoints, key=lambda endpoint: (endpoint.priority, endpoint.kind, endpoint.path, endpoint.name))


class LlmsTxtView(View):
    """Serve an automatically generated llms.txt document."""

    def get_site_title(self) -> str:
        """Return site title used by llms.txt header.

        :returns: Site title.
        """
        return str(_setting("SITE_TITLE", "Django Site"))

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Render llms.txt from discovered ViewForAgents routes.

        :param request: The incoming HTTP request.
        :returns: Plain-text llms.txt response.
        """
        endpoints = collect_llms_endpoints()
        lines = [
            f"# {self.get_site_title()}",
            "",
            "Agent-ready endpoint index discovered from Django URL configuration.",
            "Use `Accept: text/markdown` to fetch markdown responses when available.",
            "",
        ]

        grouped: dict[str, list[LlmsEndpoint]] = {}
        for endpoint in endpoints:
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
        return HttpResponse(document, content_type="text/plain; charset=utf-8")
