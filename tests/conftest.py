"""Shared fixtures for Alibaba Cloud Magic Modules tests."""

import textwrap
from pathlib import Path

import pytest

DEFINITIONS_DIR = Path(__file__).resolve().parent.parent / "definitions"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "generator" / "templates"


@pytest.fixture()
def tmp_definition(tmp_path):
    """Return a helper that writes a YAML string to a temp file and returns its path."""

    def _write(content: str, filename: str = "test_resource.yaml") -> Path:
        p = tmp_path / filename
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    return _write


@pytest.fixture()
def minimal_yaml():
    """Minimal valid YAML definition."""
    return """\
        name: TestWidget
        module_name: alicloud_testwidget
        description: "Manage test widgets"
        product: Ecs
        api_version: "2014-05-26"
        create_action: CreateWidget
        describe_action: DescribeWidgets
        delete_action: DeleteWidget
        id_field: WidgetId
        properties:
          name:
            type: str
            required: true
            description: "Widget name."
          widget_type:
            type: str
            description: "Widget type."
            choices: [standard, premium]
    """
