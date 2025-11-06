"""ClickUp publisher implementation."""

import re
from typing import Any, Optional

import requests

from src.core.cache import CacheManager
from src.core.config import ClickUpConfig
from src.core.logger import get_logger
from src.publishers.base import BasePublisher, PublishResult
from src.publishers.field_resolver import FieldResolver
from src.scrapers.base import Alert

logger = get_logger(__name__)


class ClickUpPublisher(BasePublisher):
    """Publisher for ClickUp tickets."""

    def __init__(self, config: ClickUpConfig, alert_rules: list = None):
        """
        Initialize ClickUp publisher.

        Args:
            config: ClickUp configuration
            alert_rules: Optional list of alert rules for tag resolution
        """
        self.config = config
        self.alert_rules = alert_rules or []
        self.session = self._create_session()
        self.cache = (
            CacheManager(config.cache.path, config.cache.ttl) if config.cache.enabled else None
        )
        self._existing_tasks = None
        self._field_resolver = None
        self._list_info = None

    def _create_session(self) -> requests.Session:
        """Create HTTP session."""
        session = requests.Session()
        session.headers.update(
            {"Authorization": self.config.token, "Content-Type": "application/json"}
        )
        return session

    def test_connection(self) -> bool:
        """Test connection to ClickUp API."""
        try:
            response = self.session.get(f"{self.config.api_url}/api/v2/list/{self.config.list_id}")
            response.raise_for_status()
            logger.info("ClickUp connection successful")
            return True
        except requests.RequestException as e:
            logger.error("ClickUp connection failed", error=str(e))
            return False

    def get_existing_tickets(self) -> list[dict[str, Any]]:
        """Get list of existing tickets from ClickUp."""
        if self._existing_tasks is not None:
            return self._existing_tasks

        try:
            # When subtasks=true, the API returns ALL tasks (main + subtasks) in one call
            params = {
                "archived": "false",
                "subtasks": "true" if self.config.check_subtasks else "false",
            }
            response = self.session.get(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}/task", params=params
            )
            response.raise_for_status()
            tasks = response.json().get("tasks", [])

            if self.config.check_subtasks:
                logger.info(f"Fetched {len(tasks)} tasks (including subtasks)")
            else:
                logger.info(f"Fetched {len(tasks)} main tasks")

            self._existing_tasks = tasks
            return self._existing_tasks
        except requests.RequestException as e:
            logger.error("Failed to fetch existing tasks", error=str(e))
            return []

    def check_existing(self, alert: Alert) -> Optional[str]:
        """Check if a ticket already exists for this alert."""
        task_name = self._generate_task_name(alert)

        # Get all tasks (subtasks are included if check_subtasks=true)
        existing_tasks = self.get_existing_tickets()

        for task in existing_tasks:
            if task.get("name") == task_name:
                return task.get("id")

        return None

    def publish(self, alert: Alert, dry_run: bool = False) -> PublishResult:
        """Publish an alert to ClickUp."""
        # Check if task already exists
        existing_id = self.check_existing(alert)
        if existing_id:
            return PublishResult(
                success=False,
                skipped=True,
                skipped_reason="Task already exists",
                ticket_id=existing_id,
                ticket_url=f"https://app.clickup.com/t/{existing_id}",
            )

        if dry_run:
            task_name = self._generate_task_name(alert)
            return PublishResult(
                success=True, skipped=True, skipped_reason=f"Dry run - would create: {task_name}"
            )

        # Create the task
        try:
            task_data = self._prepare_task_data(alert)
            response = self.session.post(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}/task", json=task_data
            )
            response.raise_for_status()

            result = response.json()
            task_id = result.get("id")

            logger.info("Task created successfully", task_id=task_id, name=task_data["name"])

            return PublishResult(
                success=True, ticket_id=task_id, ticket_url=f"https://app.clickup.com/t/{task_id}"
            )

        except requests.RequestException as e:
            logger.error("Failed to create task", error=str(e))
            return PublishResult(success=False, error=str(e))

    def _generate_task_name(self, alert: Alert) -> str:
        """Generate task name from alert."""
        base_name = f"[{alert.customer_id}][{alert.vm}]"

        # Determine alert type from description
        alert_type = self._determine_alert_type(alert.description)
        if alert_type:
            return f"{base_name} {alert_type}"

        return base_name

    def _determine_alert_type(self, description: str) -> Optional[str]:
        """Determine alert type from description."""
        patterns = {
            "backup failed": [r"backup\s+failed", r"backup.*error"],
            "alerte stockage": [r"partition", r"disk.*space", r"disk.*usage", r"storage"],
            "alerte mémoire": [r"memory\s+usage", r"ram", r"memory.*high"],
            "alerte CPU": [r"cpu\s+usage", r"processor", r"cpu.*high"],
            "alerte systemd service": [r"systemd", r"service.*down", r"service.*failed"],
            "alerte certificat": [r"certificate.*expire", r"ssl", r"cert.*expire", r"expire.*days"],
            "server down": [r"instance.*down", r"server.*unreachable", r"instance.*unreachable"],
            "alerte RAID": [r"raid.*degraded", r"raid.*failed", r"raid.*error"],
        }

        for alert_type, regex_patterns in patterns.items():
            for pattern in regex_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return alert_type

        return None

    def _get_field_resolver(self) -> FieldResolver:
        """Get or create field resolver."""
        if self._field_resolver is None:
            fields = self.get_field_definitions()
            self._field_resolver = FieldResolver(fields)
        return self._field_resolver

    def _get_list_info(self) -> dict[str, Any]:
        """Get list information including statuses."""
        if self._list_info is None:
            try:
                response = self.session.get(
                    f"{self.config.api_url}/api/v2/list/{self.config.list_id}"
                )
                response.raise_for_status()
                self._list_info = response.json()
            except requests.RequestException as e:
                logger.error("Failed to fetch list info", error=str(e))
                self._list_info = {}
        return self._list_info

    def _prepare_task_data(self, alert: Alert) -> dict[str, Any]:
        """Prepare task data for ClickUp API."""
        task_name = self._generate_task_name(alert)

        # Get the initial status dynamically
        list_info = self._get_list_info()
        resolver = self._get_field_resolver()

        # Get the first "open" type status or fallback to first status
        initial_status = resolver.get_status_name(list_info.get("statuses", []), "open") or "To Do"

        task_data = {
            "name": task_name,
            "description": alert.description,
            "status": initial_status,
            "priority": self._map_priority(alert.severity),
        }

        # Add custom fields if configured
        custom_fields = self._get_custom_fields(alert)
        if custom_fields:
            task_data["custom_fields"] = custom_fields

        # Add tags if configured
        tags = self._collect_tags(alert)
        if tags:
            task_data["tags"] = tags

        return task_data

    def _map_priority(self, severity: str) -> int:
        """Map severity to ClickUp priority."""
        mapping = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        return mapping.get(severity.lower(), 3)

    def _get_custom_fields(self, alert: Alert) -> list[dict[str, Any]]:
        """Get custom fields for the task using dynamic field resolution."""
        custom_fields = []
        resolver = self._get_field_resolver()

        # Check if required_fields is configured
        if not hasattr(self.config, "required_fields") or not self.config.required_fields:
            logger.debug("No required_fields configured, using defaults")
            # Use sensible defaults
            self._add_default_fields(custom_fields, alert, resolver)
            return custom_fields

        required_fields = self.config.required_fields

        # Process each configured field
        for field_key, field_config in required_fields.items():
            if not isinstance(field_config, dict):
                continue

            field_name = field_config.get("field_name")
            if not field_name:
                logger.warning(f"No field_name for {field_key}")
                continue

            # Get field ID dynamically
            field_id = resolver.get_field_id(field_name)
            if not field_id:
                logger.warning(f"Field '{field_name}' not found in ClickUp")
                continue

            # Determine the value
            value = self._get_field_value(field_config, alert, resolver)
            if value is not None:
                custom_fields.append({"id": field_id, "value": value})

        return custom_fields

    def _add_default_fields(
        self, custom_fields: list[dict[str, Any]], alert: Alert, resolver: FieldResolver
    ):
        """Add default fields when no configuration is provided."""
        # No default fields - rely on configuration
        pass

    def _get_field_value(self, field_config: dict[str, Any], alert: Alert, resolver: FieldResolver):
        """Get the value for a field based on configuration."""
        field_name = field_config.get("field_name")

        # Check if it's a dropdown/labels field that needs option resolution
        if "mapping" in field_config:
            # This field has alert type mapping
            alert_type = self._determine_alert_type(alert.description)
            alert_type_key = (
                alert_type.replace("alerte ", "").replace(" ", "_") if alert_type else None
            )

            # Get the option name from mapping
            option_name = None
            if alert_type_key and alert_type_key in field_config["mapping"]:
                option_name = field_config["mapping"][alert_type_key]
            elif "default" in field_config:
                option_name = field_config["default"]

            if option_name:
                # Resolve option name to ID
                return resolver.get_option_id(field_name, option_name)

        elif "default" in field_config:
            # Simple default value - resolve if it's an option
            default_value = field_config["default"]

            # Try to resolve as option ID first
            option_id = resolver.get_option_id(field_name, default_value)
            if option_id:
                return option_id

            # Otherwise return as is
            return default_value

        elif field_config.get("use_customer_id"):
            # Special case for hospital field
            if alert.customer_id:
                # For labels field, try to find the option
                option_id = resolver.get_option_id(field_name, alert.customer_id)
                if option_id:
                    # Labels field expects an array
                    if field_config.get("type") == "labels":
                        return [option_id]
                    return option_id

        return None

    def _map_alert_to_support_type(self, alert: Alert) -> str:
        """Map alert to a support type."""
        alert_type = self._determine_alert_type(alert.description)

        # Default mapping
        type_mapping = {
            "backup failed": "Issue",
            "alerte stockage": "Problème espace disque",
            "alerte mémoire": "Issue",
            "alerte CPU": "Issue",
            "alerte systemd service": "Services Down",
            "alerte certificat": "Issue",
            "server down": "Services Down",
            "alerte RAID": "Problème espace disque",
        }

        return type_mapping.get(alert_type, "Issue")

    def _collect_tags(self, alert: Alert) -> list[str]:
        """
        Collect all tags for an alert (default + dynamic + rule-specific).

        Args:
            alert: Alert object

        Returns:
            List of tag strings
        """
        tags = []

        # Add default tags
        if self.config.default_tags:
            tags.extend(self.config.default_tags)

        # Add dynamic tags with variable resolution
        if self.config.dynamic_tags:
            for tag_template in self.config.dynamic_tags:
                resolved_tag = self._resolve_dynamic_tag(tag_template, alert)
                if resolved_tag:
                    tags.append(resolved_tag)

        # Add rule-specific tags
        matching_rule = self._find_matching_rule(alert)
        if matching_rule and matching_rule.tags:
            tags.extend(matching_rule.tags)

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    def _resolve_dynamic_tag(self, tag_template: str, alert: Alert) -> Optional[str]:
        """
        Resolve dynamic variables in a tag template.

        Args:
            tag_template: Tag template with variables like {severity}, {customer_id}
            alert: Alert object

        Returns:
            Resolved tag string or None if resolution fails
        """
        context = {
            "customer_id": alert.customer_id,
            "vm": alert.vm,
            "severity": alert.severity,
            "instance": alert.instance or "",
        }

        # Add labels to context
        for key, value in alert.labels.items():
            context[f"label_{key}"] = value

        # Add annotations to context
        for key, value in alert.annotations.items():
            context[f"annotation_{key}"] = value

        try:
            return tag_template.format(**context)
        except KeyError as e:
            logger.warning(
                "Failed to resolve tag template variable",
                template=tag_template,
                error=str(e),
            )
            return None

    def _find_matching_rule(self, alert: Alert):
        """
        Find the first matching alert rule for an alert.

        Args:
            alert: Alert to match

        Returns:
            Matching AlertRule or None
        """
        for rule in self.alert_rules:
            if self._matches_alert_rule(alert, rule):
                return rule
        return None

    def _matches_alert_rule(self, alert: Alert, rule) -> bool:
        """
        Check if alert matches a rule.

        Args:
            alert: Alert to check
            rule: AlertRule to match against

        Returns:
            True if alert matches rule
        """
        description = alert.description

        for pattern in rule.patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return True

        return False

    def get_field_definitions(self) -> dict[str, Any]:
        """Get field definitions from ClickUp API."""
        if self.cache:
            # Try to get from cache first
            cached_data = self.cache.get("fields")
            if cached_data:
                return cached_data

        try:
            response = self.session.get(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}/field"
            )
            response.raise_for_status()
            fields = response.json().get("fields", [])

            if self.cache:
                self.cache.set(fields, "fields")

            return fields

        except requests.RequestException as e:
            logger.error("Failed to fetch field definitions", error=str(e))
            return []
