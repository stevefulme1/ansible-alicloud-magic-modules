"""Validate all YAML definitions in the definitions/ directory.

This test suite ensures every shipped definition parses without errors
and that the generated Python output compiles cleanly.
"""

import py_compile
from pathlib import Path

import pytest

from generator.parser import parse_file
from generator.renderer import ModuleRenderer
from tests.conftest import DEFINITIONS_DIR, TEMPLATES_DIR

YAML_FILES = sorted(DEFINITIONS_DIR.glob("*.yaml"))
# Exclude _schema.yaml and any other underscore-prefixed reference files
YAML_FILES = [f for f in YAML_FILES if not f.name.startswith("_")]


@pytest.fixture(scope="module")
def renderer():
    return ModuleRenderer(TEMPLATES_DIR)


@pytest.mark.parametrize(
    "yaml_file",
    YAML_FILES,
    ids=[f.stem for f in YAML_FILES],
)
class TestDefinitions:
    def test_parses_without_error(self, yaml_file):
        defn = parse_file(yaml_file)
        assert defn.name
        assert defn.module_name
        assert defn.product
        assert defn.api_version

    def test_has_properties(self, yaml_file):
        defn = parse_file(yaml_file)
        assert len(defn.properties) > 0, (
            f"{yaml_file.name}: definition has no properties"
        )

    def test_generates_compilable_module(self, yaml_file, renderer, tmp_path):
        defn = parse_file(yaml_file)
        output = renderer.render_module(defn)
        p = tmp_path / f"{defn.module_name}.py"
        p.write_text(output, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)

    def test_generates_compilable_info_module(self, yaml_file, renderer, tmp_path):
        defn = parse_file(yaml_file)
        if not defn.generate_info:
            pytest.skip("generate_info is False")
        output = renderer.render_info_module(defn)
        p = tmp_path / f"{defn.module_name}_info.py"
        p.write_text(output, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)
