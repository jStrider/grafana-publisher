"""Tests for field resolver."""

import pytest
from src.publishers.field_resolver import FieldResolver


class TestFieldResolver:
    """Test field resolver functionality."""

    @pytest.fixture
    def sample_fields(self):
        """Sample field definitions."""
        return [
            {
                "id": "field-1",
                "name": "Type support",
                "type": "drop_down",
                "type_config": {
                    "options": [
                        {"id": "opt-1", "name": "Issue"},
                        {"id": "opt-2", "name": "Bug"},
                    ]
                },
            },
            {
                "id": "field-2",
                "name": "Hospital",
                "type": "labels",
                "type_config": {
                    "options": [
                        {"id": "label-1", "label": "CHU Lille"},
                        {"id": "label-2", "label": "CHU Reims"},
                    ]
                },
            },
        ]

    def test_get_field_id(self, sample_fields):
        """Test field ID resolution."""
        resolver = FieldResolver(sample_fields)

        # Exact match
        assert resolver.get_field_id("Type support") == "field-1"

        # Case insensitive
        assert resolver.get_field_id("type support") == "field-1"

        # Not found
        assert resolver.get_field_id("Unknown Field") is None

    def test_get_option_id(self, sample_fields):
        """Test option ID resolution."""
        resolver = FieldResolver(sample_fields)

        # Dropdown field
        assert resolver.get_option_id("Type support", "Issue") == "opt-1"
        assert resolver.get_option_id("Type support", "Bug") == "opt-2"

        # Labels field
        assert resolver.get_option_id("Hospital", "CHU Lille") == "label-1"

        # Not found
        assert resolver.get_option_id("Type support", "Unknown") is None

    def test_get_status_name(self):
        """Test status name resolution."""
        resolver = FieldResolver([])

        statuses = [
            {"status": "To Do", "type": "open"},
            {"status": "In Progress", "type": "custom"},
            {"status": "Done", "type": "closed"},
        ]

        assert resolver.get_status_name(statuses, "open") == "To Do"
        assert resolver.get_status_name(statuses, "custom") == "In Progress"
        assert resolver.get_status_name(statuses, "closed") == "Done"

        # Default to first if not found
        assert resolver.get_status_name(statuses, "unknown") == "To Do"
