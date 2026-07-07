========
Settings
========

All settings use the ``FOR_AGENTS_`` prefix.

FOR_AGENTS_SITE_TITLE
=====================

- Default: current Django ``Site.name`` when ``django.contrib.sites`` is installed and configured, otherwise ``"Site"``
- Used by ``llms.txt`` header title.

FOR_AGENTS_LLMS_INTRO
=====================

- Default: ``"Use `Accept: text/markdown` to fetch markdown responses when available."``
- Introductory line shown below the site title in ``llms.txt``.
- Set to an empty string to omit it entirely.
- Set to any custom string to brand or tailor the index for agents.

FOR_AGENTS_DEV_TOGGLE_PARAM
===========================

- Default: ``"for_agents"``
- Query parameter for debug markdown toggle.

FOR_AGENTS_MAX_CONSECUTIVE_BLANK_LINES
=======================================

- Default: ``1``
- Controls markdown response whitespace normalization.
- ``0`` means no blank lines between blocks.
- Negative values disable blank-line collapsing.

FOR_AGENTS_CONTENT_SIGNAL
=========================

- Default: ``"ai-train=yes, search=yes, ai-input=yes"``
- ``Content-Signal`` header emitted on markdown responses, following the
  framework defined at https://contentsignals.org/.
- Set to an empty string to disable the header.
- Customize to express your site's AI usage preferences, e.g.
  ``"ai-train=no, search=yes, ai-input=yes"``.
