Changelog
=========

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning.

## [Unreleased]


## [0.0.2] - 2026-07-07

### Added

- JSON content negotiation for ``llms.txt`` via ``Accept: application/llms+json``.
- ``FOR_AGENTS_LLMS_INTRO`` setting to customize or disable the ``llms.txt`` intro line.
- ``x-markdown-tokens`` response header on markdown responses for agent context planning.
- ``x-original-tokens`` response header on fallback responses, reporting the estimated token count of the original HTML so agents can measure token savings.
- ``Content-Signal`` response header on markdown responses, following the framework at https://contentsignals.org/. Defaults to Cloudflare's ``ai-train=yes, search=yes, ai-input=yes`` and is configurable via ``FOR_AGENTS_CONTENT_SIGNAL``.
- JSON-LD preservation: ``<script type="application/ld+json">`` blocks are kept and appended as a fenced ``json`` code block when using the HTML-to-Markdown fallback, mirroring Cloudflare's Markdown for Agents output format.
- ``Vary: Accept`` on the ``llms.txt`` response so text and JSON variants cache separately.
- 501 Not Implemented response when markdown cannot be produced (no ``.md`` template, no ``markdownify``, no ``agent_markdown`` context value), with an explanatory markdown body so agents can fall back to HTML.
- Documentation explaining the markdown body resolution order and the optional ``markdownify`` dependency.
- HTML-to-Markdown fallback using ``markdownify`` when no matching ``.md`` template exists.

### Changed

- ``__version__`` is now derived from package metadata instead of being hardcoded.
- ``Accept`` header parsing honors ``q`` values; ``text/markdown;q=0`` correctly rejects markdown.
- ``markdownify`` is now an optional dependency. Install with ``django-for-agents[markdown]`` when using the HTML fallback.
- ``llms.py`` split into a ``llms`` package with focused ``discovery`` and ``view`` modules.
- Site title fallback now prefers the current Django ``Site.name`` when ``django.contrib.sites`` is installed.
- Removed Django-specific copy from the ``llms.txt`` header in favor of a framework-neutral, configurable intro.

## [0.0.1] - 2026-07-03

### Added

- Initial django-for-agents package release.
- ViewForAgents class for template-driven markdown responses.
- Automatic llms.txt endpoint discovery and generation.
- Template filter helpers for markdown URL handling.
- Test suite with pytest and type checks with mypy.
- Sphinx docs and Read the Docs configuration.
- Tag-based release workflow for PyPI publishing.


[unreleased]: https://github.com/eillarra/django-for-agents/compare/0.0.2...HEAD
[0.0.2]: https://github.com/eillarra/django-for-agents/releases/tag/0.0.2
[0.0.1]: https://github.com/eillarra/django-for-agents/releases/tag/0.0.1
