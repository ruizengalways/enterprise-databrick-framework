from __future__ import annotations

import importlib.metadata
import tomllib
from pathlib import Path

import edp_framework

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_version_matches_project_and_installed_metadata() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]

    installed_version = importlib.metadata.version("enterprise-databricks-framework")
    assert project_version == installed_version
    assert edp_framework.__version__ == installed_version
