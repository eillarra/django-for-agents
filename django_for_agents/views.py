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

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the view and agent-response bookkeeping.

        :param kwargs: Keyword arguments passed to ``TemplateView``.
        """
        super().__init__(**kwargs)
        self._last_rendered_html: str = ""

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
        """Return True when ``Accept`` explicitly accepts markdown.

        Only an explicit ``text/markdown`` media range (with ``q > 0``)
        triggers a Markdown response. Wildcards are ignored, because real
        agents always ask for ``Accept: text/markdown`` explicitly, and
        browsers use ``*/*`` alongside ``text/html``.

        :param request: Incoming HTTP request.
        :returns: True when markdown is explicitly accepted.
        """
        accept_header = request.headers.get("Accept", "")
        if not accept_header:
            return False

        for item in accept_header.split(","):
            token = item.strip()
            if not token:
                continue

            media_range, *params = token.split(";")
            media_range = media_range.strip().lower()
            if media_range != "text/markdown":
                continue

            q = 1.0
            for param in params:
                param = param.strip()
                if param.startswith("q="):
                    try:
                        q = float(param[2:])
                    except ValueError:
                        q = 0.0

            if q > 0:
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

    def get_html_template_name(self, request: HttpRequest, context: dict[str, Any]) -> str | None:
        """Return the HTML template name used for fallback markdown conversion.

        :param request: Incoming HTTP request.
        :param context: Render context.
        :returns: HTML template name or None.
        """
        template_name = getattr(self, "template_name", "")
        if not template_name:
            return None
        return str(template_name)

    def convert_html_to_markdown(self, html: str) -> str:
        """Convert rendered HTML into a basic markdown fallback.

        Preserves JSON-LD ``<script>`` blocks by appending them as a fenced
        ``json`` code block at the end, matching Cloudflare's Markdown for
        Agents output format. All other ``<script>`` and ``<style>`` content
        is stripped during HTML processing by ``markdownify``.

        :param html: Rendered HTML string.
        :returns: Markdown text derived from the HTML.
        :raises ImproperlyConfigured: when ``markdownify`` is not installed.
        """
        try:
            from markdownify import markdownify as html_to_markdown
        except ModuleNotFoundError as exc:
            raise ImproperlyConfigured(
                "No markdown template and 'markdownify' is not installed. "
                "Install it with `pip install django-for-agents[markdown]`, "
                "or provide a matching .md template."
            ) from exc

        json_ld = self._extract_json_ld(html)
        markdown = html_to_markdown(html, heading_style="ATX", bullets="-").strip()

        if json_ld:
            markdown += f"\n\n```json\n{json_ld}\n```"

        return markdown

    @staticmethod
    def _extract_json_ld(html: str) -> str:
        """Extract and concatenate JSON-LD blocks from rendered HTML.

        Matches ``<script type="application/ld+json">...</script>`` blocks
        and joins their contents, one per line. This mirrors Cloudflare's
        Markdown for Agents behaviour.

        :param html: Rendered HTML string.
        :returns: Concatenated JSON-LD content, or empty string if none found.
        """
        import re

        pattern = re.compile(
            r'<script\s+[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        blocks = [match.strip() for match in pattern.findall(html) if match.strip()]
        return "\n".join(blocks)

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

        html_template_name = self.get_html_template_name(request, context)
        if html_template_name:
            html = render_to_string(html_template_name, context=context, request=request)
            self._last_rendered_html = html
            return self.convert_html_to_markdown(html)

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

    def get_content_signal(self, request: HttpRequest) -> str:
        """Return the ``Content-Signal`` header value for markdown responses.

        Follows the framework defined at https://contentsignals.org/. Signals
        express the website operator's preferences for how the content may be
        used after being accessed by AI systems. The default mirrors
        Cloudflare's Markdown for Agents and signals that the content is
        available for AI training, search results, and agentic input.

        :param request: Incoming HTTP request.
        :returns: Content-Signal header value string, empty to disable.
        """
        return str(_setting("CONTENT_SIGNAL", "ai-train=yes, search=yes, ai-input=yes"))

    def render_markdown_response(self, request: HttpRequest, context: dict[str, Any]) -> HttpResponse:
        """Render and return markdown HTTP response.

        If the markdown body cannot be produced (missing ``markdownify`` and no
        ``.md`` template or ``agent_markdown`` context value), a 501 response
        is returned instead of letting ``ImproperlyConfigured`` surface as 500.

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

        try:
            body = self.get_markdown_body(request, context)
        except ImproperlyConfigured as exc:
            return self.render_markdown_not_implemented_response(request, str(exc))

        if body:
            markdown_parts.append(body)

        document = "\n\n".join(markdown_parts).strip() + "\n"
        document = self.normalize_markdown_output(document)

        response = HttpResponse(document, content_type="text/markdown; charset=utf-8")
        patch_vary_headers(response, ("Accept",))

        markdown_tokens = self._estimate_token_count(document)
        response.headers["x-markdown-tokens"] = str(markdown_tokens)

        original_html = self._last_rendered_html
        if original_html:
            response.headers["x-original-tokens"] = str(self._estimate_token_count(original_html))

        content_signal = self.get_content_signal(request)
        if content_signal:
            response.headers["Content-Signal"] = content_signal

        return response

    def render_markdown_not_implemented_response(self, request: HttpRequest, reason: str) -> HttpResponse:
        """Return a 501 explaining that markdown could not be produced.

        Used when the markdown body cannot be built: the optional
        ``markdownify`` dependency is missing and no ``.md`` template or
        ``agent_markdown`` context value is available. Returning 501 (rather
        than letting ``ImproperlyConfigured`` surface as a 500) keeps the
        failure honest — the client asked for a representation the server
        cannot currently produce — and lets agents fall back to HTML.

        :param request: Incoming HTTP request.
        :param reason: Human-readable explanation of the missing piece.
        :returns: Markdown 501 response with a short explanatory body.
        """
        body = f"# Markdown not available\n\n{reason}\n"
        response = HttpResponse(body, status=501, content_type="text/markdown; charset=utf-8")
        patch_vary_headers(response, ("Accept",))
        return response

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        """Estimate the token count of a string for agent use.

        Uses a heuristic of roughly 4 characters per token, which is a common
        approximation for mixed English/code content. Aligns with the
        ``x-markdown-tokens`` / ``x-original-tokens`` headers exposed by
        Cloudflare's Markdown for Agents.

        :param text: Input text to estimate.
        :returns: Estimated token count.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

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
