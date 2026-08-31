"""Enterprise Databricks Framework reusable framework."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("enterprise-databricks-framework")
except PackageNotFoundError:  # pragma: no cover - source tree without installation
    __version__ = "0+unknown"
