"""Template filters for django-for-agents markdown templates."""

from typing import Any

from django import template
from django.http import HttpRequest


register = template.Library()


@register.filter(name="absolute_url")
def absolute_url(value: str, request: HttpRequest | Any) -> str:
    """Convert a path-like URL to an absolute URL when request is available.

    :param value: URL path or URL string.
    :param request: Current HTTP request.
    :returns: Absolute URL when possible.
    """
    if not value:
        return ""

    url = str(value)
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url

    if isinstance(request, HttpRequest):
        return request.build_absolute_uri(url)

    return url
