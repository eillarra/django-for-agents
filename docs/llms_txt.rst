========
llms.txt
========

django-for-agents provides a built-in ``/llms.txt`` endpoint via:

.. code-block:: python

  path("", include("django_for_agents.urls"))

Discovery behavior
==================

- Walks Django URL resolver patterns recursively.
- Includes class-based views that subclass ``ViewForAgents``.
- Excludes auth-only views in auto mode.
- Excludes parameterized routes by default unless explicitly enabled.

Curating large sites
====================

If you use ``ViewForAgents`` as a broad site-wide base class, ``llms.txt`` may
include more public pages than you actually want to advertise.

In that setup, mark utility, status, or low-value pages with
``include_in_llms = False`` and opt in only the pages that should appear in the
generated index.

Entry metadata
==============

Each endpoint can expose:

- title
- kind (section)
- description
- priority

Configure per-view via ``llms_*`` class attributes.
