"""CLI entry point for the Alibaba Cloud Magic Modules generator."""

import argparse
import sys
from pathlib import Path

from .parser import DefinitionError, ResourceDefinition, parse_file
from .renderer import ModuleRenderer


def _discover_definitions(definitions_dir: Path) -> list[Path]:
    paths = sorted(definitions_dir.glob("*.yaml"))
    return [p for p in paths if not p.name.startswith("_")]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alicloud-magic-modules",
        description="Generate Ansible modules for Alibaba Cloud from YAML resource definitions.",
    )
    parser.add_argument("-d", "--definitions", type=Path, default=Path("definitions"))
    parser.add_argument("-o", "--output", type=Path, default=Path("output"))
    parser.add_argument("-t", "--templates", type=Path, default=None)
    parser.add_argument("-r", "--resource", type=str, default=None)
    parser.add_argument("--info", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    return parser


def _resolve_template_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    return Path(__file__).resolve().parent / "templates"


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    definitions_dir: Path = args.definitions
    output_dir: Path = args.output
    template_dir = _resolve_template_dir(args.templates)

    if not definitions_dir.is_dir():
        print(f"error: definitions directory not found: {definitions_dir}", file=sys.stderr)
        sys.exit(1)

    yaml_files = _discover_definitions(definitions_dir)
    if not yaml_files:
        print(f"warning: no YAML files found in {definitions_dir}", file=sys.stderr)
        sys.exit(0)

    definitions: list[ResourceDefinition] = []
    errors: list[str] = []

    for yf in yaml_files:
        try:
            defn = parse_file(yf)
        except DefinitionError as exc:
            errors.append(str(exc))
            continue
        if args.resource and defn.module_name != args.resource:
            continue
        definitions.append(defn)

    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        if args.validate:
            sys.exit(1)

    if args.validate:
        for defn in definitions:
            print(f"ok: {defn.module_name} ({len(defn.properties)} properties)")
        sys.exit(0)

    if not definitions:
        print("nothing to generate (no matching definitions)", file=sys.stderr)
        sys.exit(0)

    if not template_dir.is_dir():
        print(f"error: templates directory not found: {template_dir}", file=sys.stderr)
        sys.exit(1)

    renderer = ModuleRenderer(template_dir)

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    for defn in definitions:
        generate_info = defn.generate_info if args.info is None else args.info

        module_code = renderer.render_module(defn)
        module_filename = f"{defn.module_name}.py"

        if args.dry_run:
            print(f"# --- {module_filename} ---")
            print(module_code)
        else:
            dest = output_dir / module_filename
            dest.write_text(module_code, encoding="utf-8")
            print(f"wrote {dest}")

        if generate_info:
            info_code = renderer.render_info_module(defn)
            info_filename = f"{defn.module_name}_info.py"

            if args.dry_run:
                print(f"\n# --- {info_filename} ---")
                print(info_code)
            else:
                dest = output_dir / info_filename
                dest.write_text(info_code, encoding="utf-8")
                print(f"wrote {dest}")
