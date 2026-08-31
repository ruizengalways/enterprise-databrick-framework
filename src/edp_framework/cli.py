from __future__ import annotations

import argparse

from edp_framework.metadata.validation import validate_path
from edp_framework.patterns.registry import PatternRegistry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edp")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate table metadata and pattern contracts")
    validate.add_argument("path")

    sub.add_parser("patterns", help="List registered pipeline patterns")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate":
        count = validate_path(args.path)
        print(f"OK: validated {count} table specification(s)")
        return

    registry = PatternRegistry()
    for definition in sorted(registry.definitions(), key=lambda item: item.id):
        print(f"{definition.id}: {definition.name} [{definition.implementation_hint}]")


if __name__ == "__main__":
    main()
