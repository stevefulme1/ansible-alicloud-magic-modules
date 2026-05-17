"""Parse YAML resource definitions into structured dataclasses."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .utils import snake_to_pascal


@dataclass
class PropertyDef:
    """A single module parameter definition."""

    name: str
    type: str
    required: bool = False
    description: str = ""
    default: Any = None
    choices: list | None = None
    api_field: str = ""
    updatable: bool = True
    no_log: bool = False
    elements: str | None = None
    suboptions: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.api_field:
            self.api_field = snake_to_pascal(self.name)


@dataclass
class ResourceDefinition:
    """Fully parsed resource definition ready for rendering."""

    name: str
    module_name: str
    description: str
    product: str
    api_version: str
    create_action: str = ""
    update_action: str = ""
    delete_action: str = ""
    describe_action: str = ""
    list_action: str = ""
    id_field: str = ""
    name_field: str = ""
    generate_info: bool = True
    author: str = "Alibaba Cloud Magic Modules (@ansible-collections)"
    doc_url: str = ""
    properties: list[PropertyDef] = field(default_factory=list)
    endpoint_template: str = ""
    api_style: str = "RPC"
    wait: bool = False
    wait_timeout: int = 300


_REQUIRED_TOP_LEVEL = {"name", "module_name", "product", "api_version"}
_VALID_TYPES = {"str", "int", "float", "bool", "list", "dict", "raw"}
_KNOWN_PROP_KEYS = {
    "name", "type", "required", "description", "default", "choices",
    "api_field", "updatable", "elements", "element_type",
    "element", "suboptions", "no_log",
}


class DefinitionError(Exception):
    """Raised when a YAML definition is invalid."""


def _normalize_properties(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        result: list[dict[str, Any]] = []
        for prop_name, prop_body in raw.items():
            entry = dict(prop_body) if isinstance(prop_body, dict) else {}
            entry.setdefault("name", prop_name)
            result.append(entry)
        return result
    return []


def _validate_property(prop: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []

    if "name" not in prop:
        errors.append(f"{path}: missing required field 'name'")
        return errors

    prop_path = f"{path}.{prop['name']}"

    if "element_type" in prop and "elements" not in prop:
        prop["elements"] = prop["element_type"]
    if "element" in prop and "elements" not in prop:
        elem = prop["element"]
        if isinstance(elem, dict):
            prop["elements"] = elem.get("type", "str")
        else:
            prop["elements"] = elem

    unknown = set(prop.keys()) - _KNOWN_PROP_KEYS
    if unknown:
        errors.append(f"{prop_path}: unknown keys: {', '.join(sorted(unknown))}")

    ptype = prop.get("type", "str")
    if ptype not in _VALID_TYPES:
        errors.append(f"{prop_path}: invalid type '{ptype}' (allowed: {_VALID_TYPES})")

    if ptype == "list" and prop.get("elements") and prop["elements"] not in _VALID_TYPES:
        errors.append(f"{prop_path}: invalid elements type '{prop['elements']}'")

    if prop.get("suboptions"):
        for sub in _normalize_properties(prop["suboptions"]):
            errors.extend(_validate_property(sub, f"{prop_path}.suboptions"))

    return errors


def _validate_definition(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _REQUIRED_TOP_LEVEL - set(data.keys())
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(sorted(missing))}")
    for prop in _normalize_properties(data.get("properties")):
        errors.extend(_validate_property(prop, "properties"))
    return errors


def _parse_property(raw: dict[str, Any]) -> PropertyDef:
    if "element_type" in raw and "elements" not in raw:
        raw["elements"] = raw["element_type"]
    if "element" in raw and "elements" not in raw:
        elem = raw["element"]
        if isinstance(elem, dict):
            raw["elements"] = elem.get("type", "str")
        else:
            raw["elements"] = elem

    suboptions = None
    if raw.get("suboptions"):
        suboptions = {}
        for sub in _normalize_properties(raw["suboptions"]):
            parsed = _parse_property(sub)
            suboptions[parsed.name] = {
                "name": parsed.name,
                "type": parsed.type,
                "required": parsed.required,
                "description": parsed.description,
                "default": parsed.default,
                "choices": parsed.choices,
                "api_field": parsed.api_field,
                "elements": parsed.elements,
                "suboptions": parsed.suboptions,
                "no_log": parsed.no_log,
            }

    return PropertyDef(
        name=raw["name"],
        type=raw.get("type", "str"),
        required=raw.get("required", False),
        description=raw.get("description", ""),
        default=raw.get("default"),
        choices=raw.get("choices"),
        api_field=raw.get("api_field", ""),
        updatable=raw.get("updatable", True),
        no_log=raw.get("no_log", False),
        elements=raw.get("elements"),
        suboptions=suboptions,
    )


def parse_file(path: str | Path) -> ResourceDefinition:
    """Parse a YAML definition file and return a ResourceDefinition."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise DefinitionError(f"{path}: expected a YAML mapping at top level")

    errors = _validate_definition(data)
    if errors:
        raise DefinitionError(f"{path}: validation errors:\n  " + "\n  ".join(errors))

    properties = [_parse_property(p) for p in _normalize_properties(data.get("properties"))]

    return ResourceDefinition(
        name=data["name"],
        module_name=data["module_name"],
        description=data.get("description", ""),
        product=data["product"],
        api_version=data["api_version"],
        create_action=data.get("create_action", ""),
        update_action=data.get("update_action", ""),
        delete_action=data.get("delete_action", ""),
        describe_action=data.get("describe_action", ""),
        list_action=data.get("list_action", ""),
        id_field=data.get("id_field", ""),
        name_field=data.get("name_field", ""),
        generate_info=data.get("generate_info", True),
        author=data.get("author", "Alibaba Cloud Magic Modules (@ansible-collections)"),
        doc_url=data.get("doc_url", ""),
        properties=properties,
        endpoint_template=data.get("endpoint_template", ""),
        api_style=data.get("api_style", "RPC"),
        wait=data.get("wait", False),
        wait_timeout=data.get("wait_timeout", 300),
    )
