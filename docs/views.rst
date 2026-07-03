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
3. ``Vary: Accept`` is applied to markdown responses.
