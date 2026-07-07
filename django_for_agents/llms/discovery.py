"""Discovery of ViewForAgents endpoints for ``llms.txt``."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.contrib.auth.mixins import AccessMixin
from django.urls import URLPattern, URLResolver, get_resolver

from ..views import ViewForAgents


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
