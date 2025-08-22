"""Dynamic field resolver for ClickUp."""

from typing import Any, Optional

from src.core.logger import get_logger

logger = get_logger(__name__)


class FieldResolver:
    """Resolves field names to IDs and option names to option IDs dynamically."""

    def __init__(self, fields: list[dict[str, Any]]):
        """
        Initialize field resolver with field definitions.

        Args:
            fields: List of field definitions from ClickUp API
        """
        self.fields = fields
        self._field_cache = {}
        self._option_cache = {}

    def get_field_id(self, field_name: str) -> Optional[str]:
        """
        Get field ID by name (case insensitive).

        Args:
            field_name: Name of the field

        Returns:
            Field ID or None if not found
        """
        if field_name in self._field_cache:
            return self._field_cache[field_name]

        # Try exact match first
        for field in self.fields:
            if field.get("name", "").lower() == field_name.lower():
                field_id = field.get("id")
                self._field_cache[field_name] = field_id
                logger.debug(f"Found field '{field_name}' with ID: {field_id}")
                return field_id

        # Try partial match
        for field in self.fields:
            if field_name.lower() in field.get("name", "").lower():
                field_id = field.get("id")
                self._field_cache[field_name] = field_id
                logger.debug(f"Found field '{field_name}' (partial match) with ID: {field_id}")
                return field_id

        logger.warning(f"Field '{field_name}' not found")
        return None

    def get_option_id(self, field_name: str, option_name: str) -> Optional[str]:
        """
        Get option ID for a dropdown/labels field.

        Args:
            field_name: Name of the field
            option_name: Name of the option

        Returns:
            Option ID or None if not found
        """
        cache_key = f"{field_name}:{option_name}"
        if cache_key in self._option_cache:
            return self._option_cache[cache_key]

        # First get the field
        field = None
        for f in self.fields:
            if f.get("name", "").lower() == field_name.lower():
                field = f
                break

        if not field:
            logger.warning(f"Field '{field_name}' not found")
            return None

        field_type = field.get("type")
        options = field.get("type_config", {}).get("options", [])

        if not options:
            logger.warning(f"Field '{field_name}' has no options")
            return None

        # Determine the key to use based on field type
        key = "label" if field_type == "labels" else "name"

        # Try exact match first (case insensitive)
        for option in options:
            if option.get(key, "").lower() == option_name.lower():
                option_id = option.get("id")
                self._option_cache[cache_key] = option_id
                logger.debug(
                    f"Found option '{option_name}' in field '{field_name}' with ID: {option_id}"
                )
                return option_id

        # Try partial match (case insensitive)
        for option in options:
            if option_name.lower() in option.get(key, "").lower():
                option_id = option.get("id")
                self._option_cache[cache_key] = option_id
                logger.debug(
                    f"Found option '{option_name}' (partial match) in field "
                    f"'{field_name}' with ID: {option_id}"
                )
                return option_id

        logger.warning(f"Option '{option_name}' not found in field '{field_name}'")
        return None

    def get_status_name(
        self, statuses: list[dict[str, Any]], status_type: str = "open"
    ) -> Optional[str]:
        """
        Get the status name for a given type.

        Args:
            statuses: List of status definitions
            status_type: Type of status (open, custom, done, closed)

        Returns:
            Status name or None if not found
        """
        for status in statuses:
            if status.get("type") == status_type:
                return status.get("status")

        # If not found, return the first status
        if statuses:
            return statuses[0].get("status")

        return None
