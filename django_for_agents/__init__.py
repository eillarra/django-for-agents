"""django-for-agents package."""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("django-for-agents")
except PackageNotFoundError:  # pragma: no cover - editable installs without metadata
    __version__ = "0.0.0"
