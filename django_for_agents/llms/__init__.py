"""llms.txt generation for django-for-agents."""

from .discovery import LlmsEndpoint, collect_llms_endpoints
from .view import LlmsTxtView, get_site_title


__all__ = [
    "LlmsEndpoint",
    "LlmsTxtView",
    "collect_llms_endpoints",
    "get_site_title",
]
