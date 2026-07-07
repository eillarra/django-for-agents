=================
ViewForAgents API
=================

Class attributes
================

- ``agent_ready_enabled``: enable/disable markdown negotiation.
- ``include_markdown_frontmatter``: include YAML frontmatter in markdown output.
- ``enable_dev_toggle``: allow debug query parameter markdown toggle.
- ``markdown_template_name``: explicit markdown template path.
- ``max_consecutive_blank_lines``: per-view whitespace normalization override.
- ``include_in_llms``: ``None`` auto / ``True`` include / ``False`` exclude.
- ``llms_title``: custom endpoint title for llms.txt output.
- ``llms_kind``: llms.txt section/group key.
- ``llms_description``: descriptive text shown in llms.txt.
- ``llms_priority``: ordering key for llms.txt sections and entries.
- ``llms_include_parameterized_routes``: include dynamic URL templates in llms.txt.

Override hooks
==============

- ``get_agent_metadata(request, context)``
- ``get_markdown_frontmatter(request, context)``
- ``get_markdown_template_name(request, context)``
- ``get_markdown_body(request, context)``
- ``normalize_markdown_output(markdown)``

Response flow
=============

1. If ``Accept: text/markdown`` (or debug toggle), render markdown.
2. Otherwise, render normal HTML response.
3. ``Vary: Accept`` is applied to both markdown and ``llms.txt`` responses.

Accept header handling
======================

Negotiation honors ``q`` values. ``text/markdown;q=0`` correctly rejects
markdown. Wildcards ``text/*`` and ``*/*`` are accepted when nothing more
specific is present.

Token-count headers
===================

Markdown responses include an ``x-markdown-tokens`` header estimating the token
count of the returned document, so agents can plan context-window usage without
parsing the body first.

When the response is produced via the HTML-to-Markdown fallback, an additional
``x-original-tokens`` header reports the estimated token count of the original
HTML, so agents can estimate token savings from the Markdown conversion.

Content-Signal header
======================

Markdown responses include a ``Content-Signal`` header following the framework
defined at https://contentsignals.org/. The default value,
``ai-train=yes, search=yes, ai-input=yes``, mirrors Cloudflare's Markdown for
Agents and signals that the content may be used for AI training, search
results, and agentic input. Customize it via ``FOR_AGENTS_CONTENT_SIGNAL``,
or set it to an empty string to suppress the header.

JSON-LD preservation
====================

When the HTML-to-Markdown fallback is used, ``<script type="application/ld+json">``
blocks from the source HTML are preserved by appending them as a fenced
``json`` code block at the end of the document. This mirrors Cloudflare's
Markdown for Agents output format and keeps structured data available to
AI systems. JSON-LD is the only ``<script>`` content preserved; all other
scripts and styles are stripped during conversion.

Optional markdownify
====================

The ``markdownify`` dependency is only required when relying on the
HTML-to-Markdown fallback path. Install it explicitly with::

  uv add 'django-for-agents[markdown]'

When every page ships a matching ``.md`` template, the dependency can be omitted.

Markdown body resolution order
==============================

When a request negotiates for markdown, ``django-for-agents`` resolves the
markdown body in the following order:

1. **Explicit markdown template** — If ``markdown_template_name`` is set or a
   matching ``.md`` file exists alongside the HTML template, it is rendered.
   If the explicit template is set but missing, Django raises
   ``ImproperlyConfigured``.
2. **HTML-to-Markdown fallback** — If no ``.md`` template exists, the HTML
   template is rendered and converted via ``markdownify``. This step requires
   the optional ``markdownify`` dependency.
3. **``agent_markdown`` context value** — If set in the view context, it is
   used as the markdown body directly.
4. **Page title** — As a last resort, the ``page_title`` context value is
   returned as a minimal markdown heading.

When neither a ``.md`` template, ``markdownify``, nor an ``agent_markdown``
context value is available, the view returns **501 Not Implemented** with a
short markdown body explaining what is missing. This keeps the failure
honest — the client asked for a representation the server cannot currently
produce — and lets agents fall back to a plain HTML request instead of
receiving a 500 error page.
