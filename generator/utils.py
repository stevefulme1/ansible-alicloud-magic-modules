"""Shared utility functions for the Alibaba Cloud Magic Modules generator."""


def snake_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))
