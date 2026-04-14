#!/usr/bin/env python3
"""Validate the format of references/actual-field-mapping.md.

This script checks that the actual-field-mapping.md file can be parsed correctly
by runtime/runtime_sources.py. It reports any missing required fields or format issues.

Usage:
    python3 scripts/validate_field_mapping.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to path so we can import runtime
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runtime import RuntimeSourceLoader  # noqa: E402


def main() -> int:
    """Validate the actual-field-mapping.md format."""
    print("Validating references/actual-field-mapping.md format...")
    print()

    try:
        loader = RuntimeSourceLoader(REPO_ROOT)
        sources = loader.load()
    except Exception as e:
        print(f"❌ Error loading runtime sources: {e}")
        return 1

    # Check required fields
    required_fields = [
        ("base_token", sources.base_token),
        ("customer_master_table_id", sources.customer_master_table_id),
        ("customer_archive_folder", sources.customer_archive_folder),
        ("meeting_notes_folder", sources.meeting_notes_folder),
        ("todo_tasklist_guid", sources.todo_tasklist_guid),
        ("todo_customer_field_guid", sources.todo_customer_field_guid),
        ("todo_priority_field_guid", sources.todo_priority_field_guid),
    ]

    missing_fields = []
    found_fields = []

    for field_name, hint in required_fields:
        if hint and hint.value:
            found_fields.append((field_name, hint.source_file, hint.value))
        else:
            missing_fields.append(field_name)

    # Print found fields
    if found_fields:
        print("✅ Found fields:")
        for field_name, source_file, value in found_fields:
            # Truncate long values for display
            display_value = value if len(value) < 40 else f"{value[:37]}..."
            print(f"   {field_name}: {display_value}")
            print(f"      (from {source_file})")
        print()

    # Check priority options
    if sources.todo_priority_options:
        print(f"✅ Priority options: {sources.todo_priority_options}")
        print()

    if sources.todo_priority_option_guids:
        print("✅ Priority option GUIDs:")
        for option, guid in sources.todo_priority_option_guids.items():
            print(f"   {option} -> {guid}")
        print()

    # Report missing fields
    if missing_fields:
        print("⚠️  Missing or unreadable fields:")
        for field_name in missing_fields:
            print(f"   - {field_name}")
        print()
        print("These fields can be provided via environment variables or")
        print("configured in the reference files. See SKILL.md for details.")
        print()

    # Warnings
    warnings = []

    if not sources.todo_priority_options:
        warnings.append(
            "Priority options not found. Check that actual-field-mapping.md contains "
            "a 'current known options:' section for 优先级."
        )

    if not sources.todo_priority_option_guids:
        warnings.append(
            "Priority option GUIDs not found. Check that actual-field-mapping.md contains "
            "option-to-GUID mappings like: `高` -> `<guid>`"
        )

    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"   {warning}")
        print()

    # Summary
    if not missing_fields and not warnings:
        print("✅ All required fields found and format is valid!")
        return 0
    elif missing_fields:
        print(f"⚠️  Validation completed with {len(missing_fields)} missing field(s)")
        return 0  # Missing fields from env vars is acceptable
    else:
        print("⚠️  Validation completed with warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
