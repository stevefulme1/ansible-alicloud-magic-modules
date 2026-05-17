"""Shared utility functions for the Alibaba Cloud Magic Modules generator."""

import re


def snake_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def pascal_to_snake(name: str) -> str:
    """Convert PascalCase to snake_case.

    Handles acronyms: VpcId -> vpc_id, DBInstanceId -> db_instance_id,
    VSwitchId -> vswitch_id, AllocationId -> allocation_id.
    """
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', result)
    return result.lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])
