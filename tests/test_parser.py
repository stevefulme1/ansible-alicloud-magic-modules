"""Tests for the YAML definition parser."""

import pytest

from generator.parser import (
    DefinitionError,
    PropertyDef,
    ResourceDefinition,
    _validate_definition,
    parse_file,
)
from generator.utils import snake_to_pascal


# ---------------------------------------------------------------------------
# Unit: snake_to_pascal
# ---------------------------------------------------------------------------


class TestSnakeToPascal:
    def test_single_word(self):
        assert snake_to_pascal("name") == "Name"

    def test_multi_word(self):
        assert snake_to_pascal("disk_size_gb") == "DiskSizeGb"

    def test_already_single(self):
        assert snake_to_pascal("id") == "Id"


# ---------------------------------------------------------------------------
# Unit: PropertyDef
# ---------------------------------------------------------------------------


class TestPropertyDef:
    def test_auto_api_field(self):
        p = PropertyDef(name="disk_size_gb", type="int")
        assert p.api_field == "DiskSizeGb"

    def test_explicit_api_field(self):
        p = PropertyDef(name="disk_size_gb", type="int", api_field="diskSizeGB")
        assert p.api_field == "diskSizeGB"

    def test_defaults(self):
        p = PropertyDef(name="x", type="str")
        assert p.required is False
        assert p.updatable is True
        assert p.choices is None
        assert p.elements is None
        assert p.suboptions is None
        assert p.no_log is False


# ---------------------------------------------------------------------------
# Integration: parse_file
# ---------------------------------------------------------------------------


class TestParseFile:
    def test_parse_minimal_definition(self, tmp_definition, minimal_yaml):
        path = tmp_definition(minimal_yaml)
        defn = parse_file(path)

        assert isinstance(defn, ResourceDefinition)
        assert defn.name == "TestWidget"
        assert defn.module_name == "alicloud_testwidget"
        assert defn.description == "Manage test widgets"
        assert defn.product == "Ecs"
        assert defn.api_version == "2014-05-26"
        assert defn.create_action == "CreateWidget"
        assert defn.describe_action == "DescribeWidgets"
        assert defn.delete_action == "DeleteWidget"
        assert defn.id_field == "WidgetId"
        assert defn.generate_info is True

        names = [p.name for p in defn.properties]
        assert "name" in names
        assert "widget_type" in names

        name_prop = next(p for p in defn.properties if p.name == "name")
        assert name_prop.required is True
        assert name_prop.type == "str"

        wt_prop = next(p for p in defn.properties if p.name == "widget_type")
        assert wt_prop.choices == ["standard", "premium"]

    def test_parse_with_all_options(self, tmp_definition):
        yaml_str = """\
            name: ComplexWidget
            module_name: alicloud_complexwidget
            description: "Manage complex widgets"
            product: Ecs
            api_version: "2014-05-26"
            create_action: CreateComplexWidget
            describe_action: DescribeComplexWidgets
            delete_action: DeleteComplexWidget
            id_field: ComplexWidgetId
            properties:
              name:
                type: str
                required: true
                description: "Widget name."
              tier:
                type: str
                description: "Widget tier."
                choices:
                  - Basic
                  - Standard
                  - Premium
              password:
                type: str
                description: "Widget password."
                no_log: true
              rules:
                type: list
                elements: dict
                description: "Widget rules."
                suboptions:
                  rule_name:
                    type: str
                    required: true
                  priority:
                    type: int
        """
        defn = parse_file(tmp_definition(yaml_str))

        tier = next(p for p in defn.properties if p.name == "tier")
        assert tier.choices == ["Basic", "Standard", "Premium"]

        pw = next(p for p in defn.properties if p.name == "password")
        assert pw.no_log is True

        rules = next(p for p in defn.properties if p.name == "rules")
        assert rules.elements == "dict"
        assert "rule_name" in rules.suboptions
        assert rules.suboptions["rule_name"]["required"] is True

    def test_missing_required_field(self, tmp_definition):
        yaml_str = """\
            name: BadWidget
            module_name: alicloud_badwidget
            api_version: "2014-05-26"
        """
        with pytest.raises(DefinitionError, match="missing required top-level fields"):
            parse_file(tmp_definition(yaml_str))

    def test_invalid_property_type(self, tmp_definition):
        yaml_str = """\
            name: BadWidget
            module_name: alicloud_badwidget
            product: Ecs
            api_version: "2014-05-26"
            properties:
              bad_prop:
                type: banana
        """
        with pytest.raises(DefinitionError, match="invalid type 'banana'"):
            parse_file(tmp_definition(yaml_str))

    def test_api_field_auto_conversion(self, tmp_definition, minimal_yaml):
        path = tmp_definition(minimal_yaml)
        defn = parse_file(path)

        wt_prop = next(p for p in defn.properties if p.name == "widget_type")
        assert wt_prop.api_field == "WidgetType"

        name_prop = next(p for p in defn.properties if p.name == "name")
        assert name_prop.api_field == "Name"

    def test_invalid_yaml_raises(self, tmp_definition):
        path = tmp_definition("not: valid: yaml: [")
        with pytest.raises(Exception):
            parse_file(path)

    def test_non_mapping_raises(self, tmp_definition):
        path = tmp_definition("- list\n- item\n")
        with pytest.raises(DefinitionError, match="expected a YAML mapping"):
            parse_file(path)

    def test_explicit_api_field_preserved(self, tmp_definition):
        yaml_str = """\
            name: Foo
            module_name: alicloud_foo
            product: Ecs
            api_version: "2014-05-26"
            properties:
              system_disk_category:
                type: str
                api_field: SystemDisk.Category
        """
        defn = parse_file(tmp_definition(yaml_str))
        prop = next(p for p in defn.properties if p.name == "system_disk_category")
        assert prop.api_field == "SystemDisk.Category"
