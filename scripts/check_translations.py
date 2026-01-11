#!/usr/bin/env python3
"""Check that all entities have translation strings defined.

This script parses entity files to find entity IDs and verifies
they have corresponding entries in strings.json.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

# Map HA entity base classes to their platform names in strings.json
ENTITY_CLASS_MAP = {
    "NumberEntity": "number",
    "SelectEntity": "select",
    "SensorEntity": "sensor",
    "ButtonEntity": "button",
    "SwitchEntity": "switch",
    "TextEntity": "text",
    "BinarySensorEntity": "binary_sensor",
}


def find_entity_ids(file_path: Path) -> list[tuple[str, str]]:
    """Extract entity IDs and their platform types from an entity file.

    Returns list of (entity_id, platform) tuples.
    """
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError as e:
        print(f"  Syntax error in {file_path}: {e}")
        return []

    entities: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Find which entity type this class inherits from
            platform = None
            for base in node.bases:
                base_name = None
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr

                if base_name and base_name in ENTITY_CLASS_MAP:
                    platform = ENTITY_CLASS_MAP[base_name]
                    break

            if not platform:
                continue

            # Find __init__ method and extract entity_id from super().__init__ call
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    for stmt in ast.walk(item):
                        # Look for super().__init__(coordinator, "entity_id")
                        if (
                            isinstance(stmt, ast.Call)
                            and isinstance(stmt.func, ast.Attribute)
                            and stmt.func.attr == "__init__"
                            and isinstance(stmt.func.value, ast.Call)
                            and isinstance(stmt.func.value.func, ast.Name)
                            and stmt.func.value.func.id == "super"
                            and len(stmt.args) >= 2
                            and isinstance(stmt.args[1], ast.Constant)
                        ):
                            entities.append((str(stmt.args[1].value), platform))  # noqa: PERF401

    return entities


def load_translations(strings_path: Path) -> dict:
    """Load strings.json and return the entity translations."""
    try:
        data = json.loads(strings_path.read_text())
        return data.get("entity", {})
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {strings_path}: {e}")
        return {}


def main() -> int:
    """Check translations and return exit code."""
    # Find project root (where strings.json lives)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    entities_dir = project_root / "custom_components" / "geekmagic" / "entities"
    strings_path = project_root / "custom_components" / "geekmagic" / "strings.json"

    if not entities_dir.exists():
        print(f"Entities directory not found: {entities_dir}")
        return 1

    if not strings_path.exists():
        print(f"strings.json not found: {strings_path}")
        return 1

    # Load existing translations
    translations = load_translations(strings_path)

    # Collect all entities from entity files
    all_entities: list[tuple[str, str, Path]] = []
    for py_file in entities_dir.glob("*.py"):
        if py_file.name in ("__init__.py", "base.py"):
            continue
        entities = find_entity_ids(py_file)
        for entity_id, platform in entities:
            all_entities.append((entity_id, platform, py_file))

    # Check for missing translations
    missing: list[tuple[str, str, Path]] = []
    for entity_id, platform, source_file in all_entities:
        platform_translations = translations.get(platform, {})
        if entity_id not in platform_translations:
            missing.append((entity_id, platform, source_file))

    # Report results
    if missing:
        print("Missing translation strings in strings.json:")
        print()
        for entity_id, platform, source_file in missing:
            print(f"  entity.{platform}.{entity_id}.name")
            print(f"    (defined in {source_file.name})")
        print()
        print("Add these entries to strings.json under the 'entity' key.")
        print()
        print("Example:")
        print("  {")
        print('    "entity": {')
        for entity_id, platform, _ in missing:
            print(f'      "{platform}": {{')
            print(f'        "{entity_id}": {{')
            print('          "name": "Entity Name Here"')
            print("        }")
            print("      }")
        print("    }")
        print("  }")
        return 1

    print(f"All {len(all_entities)} entities have translations defined.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
