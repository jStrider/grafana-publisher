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
            "status": "nouvelles demandes",  # ClickUp status in French
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
        
        # Check if required_fields is configured
        if not hasattr(self.config, 'required_fields'):
            logger.warning("No required_fields configured in ClickUp settings")
            return custom_fields
        
        required_fields = self.config.required_fields
        
        # Determine alert type for mapping
        alert_type = self._determine_alert_type(alert.description)
        
        # Process Type support field
        if 'type_support' in required_fields:
            field_config = required_fields['type_support']
            
            # Map alert type to support type
            alert_type_key = alert_type.replace("alerte ", "").replace(" ", "_") if alert_type else None
            
            # Get value from mapping or use default
            value = field_config.get('default', 'Monitoring')
            if alert_type_key and 'mapping' in field_config:
                value = field_config['mapping'].get(alert_type_key, value)
            
            custom_fields.append({
                "id": field_config['field_id'],
                "value": value
            })
        
        # Process Type Infra field
        if 'type_infra' in required_fields:
            field_config = required_fields['type_infra']
            custom_fields.append({
                "id": field_config['field_id'],
                "value": field_config.get('default', 'monitoring')
            })
        
        # Process categorie infra field
        if 'categorie_infra' in required_fields:
            field_config = required_fields['categorie_infra']
            custom_fields.append({
                "id": field_config['field_id'],
                "value": field_config.get('default', 'Operationnel')
            })
        
        # Process Hospital field - disabled for now as it's causing issues
        # The field is of type 'labels' but doesn't have predefined options
        # TODO: Investigate how to properly set label fields in ClickUp
        # if 'hospital' in required_fields:
        #     field_config = required_fields['hospital']
        #     
        #     # Use customer_id if configured
        #     if field_config.get('use_customer_id', False):
        #         value = alert.customer_id.title() if alert.customer_id else "Sancare"
        #         
        #         # For labels type, value should be an array
        #         if field_config.get('type') == 'labels':
        #             value = [value]
        #         
        #         custom_fields.append({
        #             "id": field_config['field_id'],
        #             "value": value
        #         })
        
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