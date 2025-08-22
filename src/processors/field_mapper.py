"""Dynamic field mapping for ticketing systems."""

from typing import Any, Dict, List, Optional

from src.core.logger import get_logger


logger = get_logger(__name__)


class FieldMapper:
    """Maps alert fields to ticketing system fields."""
    
    def __init__(self, field_definitions: List[Dict], mappings: Dict[str, Any]):
        """
        Initialize field mapper.
        
        Args:
            field_definitions: Field definitions from ticketing system
            mappings: Field mapping configuration
        """
        self.field_definitions = field_definitions
        self.mappings = mappings
        self._field_cache = self._build_field_cache()
    
    def _build_field_cache(self) -> Dict[str, Dict]:
        """Build cache of field definitions by name."""
        cache = {}
        for field in self.field_definitions:
            name = field.get("name", "").lower()
            cache[name] = field
        return cache
    
    def map_fields(self, alert_data: Dict, custom_values: Dict = None) -> List[Dict]:
        """
        Map alert data to custom fields.
        
        Args:
            alert_data: Processed alert data
            custom_values: Optional custom field values
            
        Returns:
            List of custom field dictionaries for API
        """
        custom_fields = []
        custom_values = custom_values or {}
        
        for field_key, mapping in self.mappings.items():
            field_name = mapping.get("field_name", "").lower()
            field_def = self._field_cache.get(field_name)
            
            if not field_def:
                logger.warning(f"Field definition not found", field=field_name)
                continue
            
            # Get value from custom values or use default
            value = custom_values.get(field_key, mapping.get("default"))
            
            if value:
                field_id = field_def.get("id")
                field_type = field_def.get("type")
                
                # Map value based on field type
                mapped_value = self._map_value(value, field_def, field_type)
                
                if mapped_value is not None:
                    custom_fields.append({
                        "id": field_id,
                        "value": mapped_value
                    })
        
        return custom_fields
    
    def _map_value(self, value: str, field_def: Dict, field_type: str) -> Optional[Any]:
        """
        Map value based on field type.
        
        Args:
            value: Value to map
            field_def: Field definition
            field_type: Type of field
            
        Returns:
            Mapped value or None
        """
        if field_type in ["drop_down", "labels"]:
            # Find matching option
            options = field_def.get("type_config", {}).get("options", [])
            return self._find_option_id(value, options, field_type)
        
        elif field_type == "text":
            return str(value)
        
        elif field_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        elif field_type == "checkbox":
            return value.lower() in ["true", "yes", "1", "on"]
        
        else:
            # Unknown field type, return as-is
            return value
    
    def _find_option_id(self, value: str, options: List[Dict], field_type: str) -> Optional[str]:
        """
        Find option ID by value.
        
        Args:
            value: Value to find
            options: List of options
            field_type: Type of field (determines key to check)
            
        Returns:
            Option ID or None
        """
        value_lower = value.lower()
        
        # Determine which key to check based on field type
        key = "label" if field_type == "labels" else "name"
        
        # First try exact match
        for option in options:
            if option.get(key, "").lower() == value_lower:
                return option.get("id")
        
        # Then try partial match
        for option in options:
            if value_lower in option.get(key, "").lower():
                return option.get("id")
        
        logger.warning(f"No matching option found", value=value, field_type=field_type)
        return None
    
    def get_field_by_name(self, name: str) -> Optional[Dict]:
        """
        Get field definition by name.
        
        Args:
            name: Field name
            
        Returns:
            Field definition or None
        """
        return self._field_cache.get(name.lower())
    
    def list_available_fields(self) -> List[str]:
        """
        List all available field names.
        
        Returns:
            List of field names
        """
        return [field.get("name") for field in self.field_definitions]
    
    def get_field_options(self, field_name: str) -> List[str]:
        """
        Get available options for a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            List of option names/labels
        """
        field_def = self._field_cache.get(field_name.lower())
        if not field_def:
            return []
        
        field_type = field_def.get("type")
        if field_type not in ["drop_down", "labels"]:
            return []
        
        options = field_def.get("type_config", {}).get("options", [])
        key = "label" if field_type == "labels" else "name"
        
        return [option.get(key) for option in options if option.get(key)]