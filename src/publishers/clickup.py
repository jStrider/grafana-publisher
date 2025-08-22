"""ClickUp publisher implementation."""

import re
from typing import Any, Dict, List, Optional

import requests

from src.core.cache import CacheManager
from src.core.config import ClickUpConfig
from src.core.logger import get_logger
from src.publishers.base import BasePublisher, PublishResult
from src.scrapers.base import Alert


logger = get_logger(__name__)


class ClickUpPublisher(BasePublisher):
    """Publisher for ClickUp tickets."""
    
    def __init__(self, config: ClickUpConfig):
        """
        Initialize ClickUp publisher.
        
        Args:
            config: ClickUp configuration
        """
        self.config = config
        self.session = self._create_session()
        self.cache = CacheManager(
            config.cache.path,
            config.cache.ttl
        ) if config.cache.enabled else None
        self._existing_tasks = None
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session."""
        session = requests.Session()
        session.headers.update({
            "Authorization": self.config.token,
            "Content-Type": "application/json"
        })
        return session
    
    def test_connection(self) -> bool:
        """Test connection to ClickUp API."""
        try:
            response = self.session.get(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}"
            )
            response.raise_for_status()
            logger.info("ClickUp connection successful")
            return True
        except requests.RequestException as e:
            logger.error("ClickUp connection failed", error=str(e))
            return False
    
    def get_existing_tickets(self) -> List[Dict[str, Any]]:
        """Get list of existing tickets from ClickUp."""
        if self._existing_tasks is not None:
            return self._existing_tasks
        
        try:
            # When subtasks=true, the API returns ALL tasks (main + subtasks) in one call
            params = {
                "archived": "false",
                "subtasks": "true" if self.config.check_subtasks else "false"
            }
            response = self.session.get(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}/task",
                params=params
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
                skipped_reason=f"Task already exists",
                ticket_id=existing_id,
                ticket_url=f"https://app.clickup.com/t/{existing_id}"
            )
        
        if dry_run:
            task_name = self._generate_task_name(alert)
            return PublishResult(
                success=True,
                skipped=True,
                skipped_reason=f"Dry run - would create: {task_name}"
            )
        
        # Create the task
        try:
            task_data = self._prepare_task_data(alert)
            response = self.session.post(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}/task",
                json=task_data
            )
            response.raise_for_status()
            
            result = response.json()
            task_id = result.get("id")
            
            logger.info("Task created successfully", 
                       task_id=task_id, 
                       name=task_data["name"])
            
            return PublishResult(
                success=True,
                ticket_id=task_id,
                ticket_url=f"https://app.clickup.com/t/{task_id}"
            )
            
        except requests.RequestException as e:
            logger.error("Failed to create task", error=str(e))
            return PublishResult(
                success=False,
                error=str(e)
            )
    
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
            "alerte RAID": [r"raid.*degraded", r"raid.*failed", r"raid.*error"]
        }
        
        for alert_type, regex_patterns in patterns.items():
            for pattern in regex_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return alert_type
        
        return None
    
    def _prepare_task_data(self, alert: Alert) -> Dict[str, Any]:
        """Prepare task data for ClickUp API."""
        task_name = self._generate_task_name(alert)
        
        task_data = {
            "name": task_name,
            "description": alert.description,
            "status": "Open",
            "priority": self._map_priority(alert.severity)
        }
        
        # Add custom fields if configured
        custom_fields = self._get_custom_fields(alert)
        if custom_fields:
            task_data["custom_fields"] = custom_fields
        
        return task_data
    
    def _map_priority(self, severity: str) -> int:
        """Map severity to ClickUp priority."""
        mapping = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4
        }
        return mapping.get(severity.lower(), 3)
    
    def _get_custom_fields(self, alert: Alert) -> List[Dict[str, Any]]:
        """Get custom fields for the task."""
        custom_fields = []
        
        # Required fields with their IDs from ClickUp
        # Type support (ID: 8daff867-e54a-49f5-...)
        # Type Infra (ID: 34e05f42-914e-41cb-...)
        # categorie infra (ID: 6b621c5f-6aff-412b-...)
        
        # Determine values based on alert type
        alert_type = self._determine_alert_type(alert.description)
        
        # Type support - map alert types to support types
        type_support_mapping = {
            "backup failed": "Sauvegarde",
            "alerte stockage": "Stockage",
            "alerte mémoire": "Performance",
            "alerte CPU": "Performance",
            "alerte systemd service": "Services Down",
            "alerte certificat": "Certificat",
            "server down": "Services Down",
            "alerte RAID": "Stockage"
        }
        
        type_support_value = type_support_mapping.get(alert_type, "Monitoring")
        
        # Add Type support field
        custom_fields.append({
            "id": "8daff867-e54a-49f5-47ba-8c16cba83070",  # Full ID for Type support
            "value": type_support_value
        })
        
        # Add Type Infra field - default to "monitoring" for alerts
        custom_fields.append({
            "id": "34e05f42-914e-41cb-9834-a67c488bc643",  # Full ID for Type Infra
            "value": "monitoring"
        })
        
        # Add categorie infra field - default to "Operationnel" for alerts
        custom_fields.append({
            "id": "6b621c5f-6aff-412b-946b-ffb64802de5e",  # Full ID for categorie infra
            "value": "Operationnel"
        })
        
        # Add Hospital field if configured
        if hasattr(self.config, 'field_mappings') and 'hospital' in self.config.field_mappings:
            # Hospital field ID: 3b500181-7b34-4062-...
            hospital_value = alert.customer_id.title() if alert.customer_id else "Sancare"
            custom_fields.append({
                "id": "3b500181-7b34-4062-9f6f-c8e088e5f1bd",  # Full ID for Hôpital
                "value": [hospital_value]  # Labels field expects array
            })
        
        return custom_fields
    
    def get_field_definitions(self) -> Dict[str, Any]:
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