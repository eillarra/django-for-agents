# Django For Agents

[![github-tests-badge]][github-tests]
[![github-mypy-badge]][github-mypy]
[![codecov-badge]][codecov]
[![pypi-badge]][pypi]
[![pypi-versions]][pypi]
[![license-badge]](LICENSE)


django-for-agents helps Django projects expose agent-friendly content:

- Markdown responses via HTTP content negotiation (`Accept: text/markdown`).
- Optional debug toggle (`?for_agents=1`) in development.
- Automatic `llms.txt` endpoint generation from your URL configuration.
- Frontmatter metadata and markdown whitespace normalization.

Supported Python versions: 3.12, 3.13, 3.14.

## Install

```bash
uv add django-for-agents
```

## Minimal setup

1. Add the app to `INSTALLED_APPS`.
2. Include `django_for_agents.urls` in your root URL config.
3. Inherit `ViewForAgents` for pages you want agent-ready.
4. Create matching `.md` templates for markdown responses.

```python
INSTALLED_APPS = [
    # ...
    "django_for_agents",
]

from django.urls import include, path

urlpatterns = [
    # ...
    path("", include("django_for_agents.urls")),
]
```

## Documentation

- Full docs source: `docs/`
- Read the Docs config: `.readthedocs.yaml`

Main docs pages:

- `docs/installation.rst`
- `docs/quickstart.rst`
- `docs/settings.rst`
- `docs/views.rst`
- `docs/llms_txt.rst`
- `docs/api.rst`

## Build and publish

```bash
uv build
uv publish
```


[github-mypy]: https://github.com/eillarra/django-for-agents/actions?query=workflow%3Amypy
[github-mypy-badge]: https://github.com/eillarra/django-for-agents/workflows/mypy/badge.svg
[github-tests]: https://github.com/eillarra/django-for-agents/actions?query=workflow%3Atests
[github-tests-badge]: https://github.com/eillarra/django-for-agents/workflows/tests/badge.svg
[codecov]: https://codecov.io/gh/eillarra/django-for-agents
[codecov-badge]: https://codecov.io/gh/eillarra/django-for-agents/branch/main/graph/badge.svg
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[pypi]: https://pypi.org/project/django-for-agents/
[pypi-badge]: https://badge.fury.io/py/django-for-agents.svg
[pypi-versions]: https://img.shields.io/pypi/pyversions/django-for-agents.svg
