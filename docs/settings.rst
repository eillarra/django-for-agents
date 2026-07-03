========
Settings
========

All settings use the ``FOR_AGENTS_`` prefix.

FOR_AGENTS_SITE_TITLE
=====================

- Default: ``"Django Site"``
- Used by ``llms.txt`` header title.

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
