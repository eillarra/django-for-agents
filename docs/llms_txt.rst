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

Entry metadata
==============

Each endpoint can expose:

- title
- kind (section)
- description
- priority

Configure per-view via ``llms_*`` class attributes.
