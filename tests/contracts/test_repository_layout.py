from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_layout() -> dict:
    return yaml.safe_load((ROOT / "project/layout.yml").read_text(encoding="utf-8"))


def test_framework_layout_has_only_real_capability_packages() -> None:
    layout = load_layout()
    package_root = ROOT / layout["package_root"]

    for module in layout["package_modules"]:
        path = package_root / module
        assert path.is_dir(), module
        python_files = [candidate for candidate in path.glob("*.py") if candidate.name != "__init__.py"]
        assert python_files, f"{module} must contain real implementation, not only __init__.py"

    for placeholder in layout["forbidden_package_placeholders"]:
        assert not (package_root / placeholder).exists(), placeholder


def test_documented_top_level_directories_exist_and_reserved_roots_do_not() -> None:
    layout = load_layout()
    for directory in layout["root"]:
        assert (ROOT / directory).is_dir(), directory
    for directory in layout["forbidden_reserved_roots"]:
        assert not (ROOT / directory).exists(), directory


def test_framework_repository_does_not_regrow_platform_or_customer_roots() -> None:
    forbidden = ["databricks.yml", "platform", "resources", "config/environments", "fixtures"]
    for relative in forbidden:
        assert not (ROOT / relative).exists(), relative
