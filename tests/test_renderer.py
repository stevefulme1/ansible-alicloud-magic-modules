"""Tests for the Jinja2 module renderer."""

import py_compile
from pathlib import Path

import pytest

from generator.parser import parse_file
from generator.renderer import (
    ModuleRenderer,
    _to_python,
    _to_python_list,
)
from generator.utils import snake_to_camel as _snake_to_camel
from generator.utils import snake_to_pascal as _snake_to_pascal
from tests.conftest import DEFINITIONS_DIR, TEMPLATES_DIR


# ---------------------------------------------------------------------------
# Unit: custom filters
# ---------------------------------------------------------------------------


class TestSnakeToCamel:
    def test_basic(self):
        assert _snake_to_camel("source_port_range") == "sourcePortRange"

    def test_single_word(self):
        assert _snake_to_camel("name") == "name"


class TestSnakeToPascal:
    def test_basic(self):
        assert _snake_to_pascal("source_port_range") == "SourcePortRange"


class TestToPython:
    def test_none(self):
        assert _to_python(None) == "None"

    def test_true(self):
        assert _to_python(True) == "True"

    def test_false(self):
        assert _to_python(False) == "False"

    def test_string(self):
        result = _to_python("hello")
        assert result == "'hello'"

    def test_int(self):
        assert _to_python(42) == "42"


class TestToPythonList:
    def test_short_list_single_line(self):
        result = _to_python_list(["a", "b", "c"], indent=16)
        assert result == "['a', 'b', 'c']"
        assert "\n" not in result

    def test_long_list_multi_line(self):
        long_choices = [f"VeryLongChoiceName_{i}" for i in range(20)]
        result = _to_python_list(long_choices, indent=16)
        assert "\n" in result
        assert result.startswith("[")
        assert result.strip().endswith("]")

    def test_all_items_present(self):
        items = ["Alpha", "Beta", "Gamma"]
        result = _to_python_list(items, indent=16)
        for item in items:
            assert f"'{item}'" in result


# ---------------------------------------------------------------------------
# Integration: ModuleRenderer
# ---------------------------------------------------------------------------


class TestModuleRenderer:
    @pytest.fixture()
    def renderer(self):
        return ModuleRenderer(TEMPLATES_DIR)

    @pytest.fixture()
    def simple_definition(self, tmp_definition, minimal_yaml):
        return parse_file(tmp_definition(minimal_yaml))

    def test_render_module(self, renderer, simple_definition):
        output = renderer.render_module(simple_definition)
        assert "DOCUMENTATION" in output
        assert "alicloud_testwidget" in output
        assert "Manage test widgets" in output
        assert "EXAMPLES" in output
        assert "RETURN" in output
        # Class name should contain the resource name
        assert "TestWidget" in output

    def test_render_info_module(self, renderer, simple_definition):
        output = renderer.render_info_module(simple_definition)
        assert "DOCUMENTATION" in output
        assert "alicloud_testwidget" in output or "TestWidget" in output

    def test_render_module_valid_python(self, renderer, simple_definition, tmp_path):
        output = renderer.render_module(simple_definition)
        p = tmp_path / "module.py"
        p.write_text(output, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)

    def test_render_info_module_valid_python(self, renderer, simple_definition, tmp_path):
        output = renderer.render_info_module(simple_definition)
        p = tmp_path / "module_info.py"
        p.write_text(output, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)

    def test_render_with_choices(self, renderer, tmp_definition):
        yaml_str = """\
            name: Foo
            module_name: alicloud_foo
            product: Ecs
            api_version: "2014-05-26"
            create_action: CreateFoo
            describe_action: DescribeFoos
            delete_action: DeleteFoo
            id_field: FooId
            properties:
              name:
                type: str
                required: true
              tier:
                type: str
                choices:
                  - Basic
                  - Standard
                  - Premium
        """
        defn = parse_file(tmp_definition(yaml_str))
        output = renderer.render_module(defn)
        assert "'Basic'" in output
        assert "'Standard'" in output
        assert "'Premium'" in output

    def test_render_with_no_log(self, renderer, tmp_definition):
        yaml_str = """\
            name: Foo
            module_name: alicloud_foo
            product: Ecs
            api_version: "2014-05-26"
            create_action: CreateFoo
            describe_action: DescribeFoos
            delete_action: DeleteFoo
            id_field: FooId
            properties:
              name:
                type: str
                required: true
              password:
                type: str
                no_log: true
                description: "Secret password."
        """
        defn = parse_file(tmp_definition(yaml_str))
        output = renderer.render_module(defn)
        assert "no_log" in output

    def test_render_module_gpl_header(self, renderer, simple_definition):
        output = renderer.render_module(simple_definition)
        assert "GNU General Public License" in output
