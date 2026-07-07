==========
Quickstart
==========

1. Add the app
==============

.. code-block:: python

  INSTALLED_APPS = [
      # ...
      "django_for_agents",
  ]

2. Include plugin URLs (llms.txt)
=================================

.. code-block:: python

  from django.urls import include, path

  urlpatterns = [
      # ...
      path("", include("django_for_agents.urls")),
  ]

3. Inherit ViewForAgents
========================

.. code-block:: python

  from django.http import HttpRequest, HttpResponse

  from django_for_agents.views import ViewForAgents


  class DocsPageView(ViewForAgents):
      template_name = "docs/page.html"
      include_in_llms = True
      llms_kind = "docs"
      llms_description = "Documentation entry points."

      def get(self, request: HttpRequest) -> HttpResponse:
          context = {
              "page_title": "Docs",
              "body": "Hello from docs",
          }
          return self.render_to_response(context)

4. Add markdown template (optional)
===================================

Given ``docs/page.html``, also create ``docs/page.md``. When the request
includes ``Accept: text/markdown``, django-for-agents renders ``.md``.

If no matching ``.md`` file exists, django-for-agents falls back to converting
the rendered HTML output into markdown automatically.

.. code-block:: django

  {% load for_agents %}

  # {{ page_title }}

  {{ body }}

  [Home]({{ "/"|absolute_url:request }})
