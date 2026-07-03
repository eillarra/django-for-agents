"""Class-based view utilities for agent-oriented markdown responses."""

from __future__ import annotations

import json
import re
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.cache import patch_vary_headers
from django.views.generic import TemplateView


def _setting(name: str, default: Any) -> Any:
    """Read plugin settings with FOR_AGENTS_ prefix.

    :param name: Setting key suffix.
    :param default: Fallback value.
    :returns: Setting value.
    """
    return getattr(settings, f"FOR_AGENTS_{name}", default)


class ViewForAgents(TemplateView):
    """Serve HTML or markdown representations for agent clients.

    Markdown representation is returned when the request includes
    ``Accept: text/markdown`` or when debug toggle is enabled and requested.
    """

    agent_ready_enabled: bool = True
    include_markdown_frontmatter: bool = True
    enable_dev_toggle: bool = False
    markdown_template_name: str | None = None
    max_consecutive_blank_lines: int | None = None

    include_in_llms: bool | None = None
    llms_title: str | None = None
    llms_kind: str = "general"
    llms_description: str = ""
    llms_priority: int = 100
    llms_include_parameterized_routes: bool = False

    def get_dev_toggle_param(self) -> str:
        """Return query parameter name used for markdown debug toggle.

        :returns: Query parameter name.
        """
        return str(_setting("DEV_TOGGLE_PARAM", "for_agents"))

    def get_max_consecutive_blank_lines(self) -> int:
        """Return max allowed consecutive blank lines in markdown output.

        :returns: Number of allowed blank lines.
        """
        if self.max_consecutive_blank_lines is not None:
            return self.max_consecutive_blank_lines
        value = _setting("MAX_CONSECUTIVE_BLANK_LINES", 1)
        return int(value)

    def wants_markdown_response(self, request: HttpRequest) -> bool:
        """Return whether request should receive markdown response.

        :param request: Incoming HTTP request.
        :returns: True when markdown output should be served.
        """
        if not self.agent_ready_enabled:
            return False
        if self._is_dev_toggle_enabled(request):
            return True
        return self._accept_header_requests_markdown(request)

    @staticmethod
    def _accept_header_requests_markdown(request: HttpRequest) -> bool:
        """Return True when ``Accept`` explicitly includes markdown.

        :param request: Incoming HTTP request.
        :returns: True when markdown media range is present.
        """
        accept_header = request.headers.get("Accept", "")
        if not accept_header:
            return False

        for item in accept_header.split(","):
            media_range = item.split(";", maxsplit=1)[0].strip().lower()
            if media_range == "text/markdown":
                return True

        return False

    def _is_dev_toggle_enabled(self, request: HttpRequest) -> bool:
        """Return True when debug mode toggle requests markdown.

        :param request: Incoming HTTP request.
        :returns: True when debug markdown toggle is active.
        """
        if not settings.DEBUG or not self.enable_dev_toggle:
            return False

        toggle_param = self.get_dev_toggle_param()
        toggle_value = str(request.GET.get(toggle_param, "")).strip().lower()
        return toggle_value in {"1", "true", "yes", "on", "md", "markdown"}

    def get_agent_ready_context(self, request: HttpRequest) -> dict[str, Any]:
        """Return helper flags for optional template debug controls.

        :param request: Incoming HTTP request.
        :returns: Dictionary with debug toggle metadata.
        """
        if not settings.DEBUG or not self.enable_dev_toggle:
            return {}

        return {
            "for_agents_dev_toggle_enabled": True,
            "for_agents_dev_toggle_param": self.get_dev_toggle_param(),
            "for_agents_is_markdown": self.wants_markdown_response(request),
        }

    def get_agent_metadata(self, request: HttpRequest, context: dict[str, Any]) -> dict[str, str]:
        """Return metadata used to build markdown frontmatter.

        :param request: Incoming HTTP request.
        :param context: Render context.
        :returns: Frontmatter-compatible key/value metadata.
        """
        metadata: dict[str, str] = {}

        page_title = context.get("page_title")
        if page_title:
            metadata["title"] = str(page_title)

        description = context.get("meta_description")
        if isinstance(description, str) and description:
            metadata["description"] = description

        image = context.get("meta_image")
        if isinstance(image, str) and image:
            metadata["image"] = image

        return metadata

    def get_markdown_frontmatter(self, request: HttpRequest, context: dict[str, Any]) -> dict[str, str]:
        """Return markdown frontmatter fields.

        :param request: Incoming HTTP request.
        :param context: Render context.
        :returns: Frontmatter fields.
        """
        metadata = self.get_agent_metadata(request, context)
        return {key: value for key, value in metadata.items() if value}

    def get_markdown_template_name(self, request: HttpRequest, context: dict[str, Any]) -> str | None:
        """Infer markdown template name from html template when not explicit.

        :param request: Incoming HTTP request.
        :param context: Render context.
        :returns: Markdown template name or None.
        """
        if self.markdown_template_name:
            return self.markdown_template_name

        template_name = getattr(self, "template_name", "")
        if not template_name:
            return None

        if template_name.endswith(".html"):
            return f"{template_name[:-5]}.md"

        return f"{template_name}.md"

    def get_markdown_body(self, request: HttpRequest, context: dict[str, Any]) -> str:
        """Return markdown body text for the response.

        :param request: Incoming HTTP request.
        :param context: Render context.
        :returns: Markdown body.
        """
        template_name = self.get_markdown_template_name(request, context)
        if template_name:
            try:
                return render_to_string(template_name, context=context, request=request).strip()
            except TemplateDoesNotExist as exc:
                if self.markdown_template_name:
                    raise ImproperlyConfigured(
                        f"Markdown template '{template_name}' not found for {self.__class__.__name__}."
                    ) from exc

        explicit_markdown = context.get("agent_markdown")
        if explicit_markdown:
            return str(explicit_markdown).strip()

        return str(context.get("page_title", "")).strip()

    def normalize_markdown_output(self, markdown: str) -> str:
        """Normalize markdown whitespace to reduce large blank gaps.

        :param markdown: Raw markdown document.
        :returns: Normalized markdown document.
        """
        max_blank = self.get_max_consecutive_blank_lines()
        if max_blank < 0:
            return markdown

        normalized = markdown.replace("\r\n", "\n")
        allowed_newlines = max_blank + 1
        min_run = allowed_newlines + 1
        pattern = rf"\n{{{min_run},}}"
        replacement = "\n" * allowed_newlines
        return re.sub(pattern, replacement, normalized)

    def render_markdown_response(self, request: HttpRequest, context: dict[str, Any]) -> HttpResponse:
        """Render and return markdown HTTP response.

        :param request: Incoming HTTP request.
        :param context: Render context.
        :returns: Markdown response.
        """
        markdown_parts: list[str] = []

        if self.include_markdown_frontmatter:
            frontmatter = self.get_markdown_frontmatter(request, context)
            if frontmatter:
                yaml_lines = ["---"]
                for key, value in frontmatter.items():
                    escaped = str(value).replace("\n", " ")
                    yaml_lines.append(f"{key}: {json.dumps(escaped, ensure_ascii=True)}")
                yaml_lines.append("---")
                markdown_parts.append("\n".join(yaml_lines))

        body = self.get_markdown_body(request, context)
        if body:
            markdown_parts.append(body)

        document = "\n\n".join(markdown_parts).strip() + "\n"
        document = self.normalize_markdown_output(document)

        response = HttpResponse(document, content_type="text/markdown; charset=utf-8")
        patch_vary_headers(response, ("Accept",))
        return response

    def render_to_response(self, context: dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        """Render HTML or markdown response based on request negotiation.

        :param context: Template render context.
        :param response_kwargs: Additional response keyword arguments.
        :returns: HTML or markdown HTTP response.
        """
        request = getattr(self, "request", None)
        if isinstance(request, HttpRequest) and self.wants_markdown_response(request):
            return self.render_markdown_response(request, context)

        response = super().render_to_response(context, **response_kwargs)
        if self.agent_ready_enabled:
            patch_vary_headers(response, ("Accept",))
        return response
