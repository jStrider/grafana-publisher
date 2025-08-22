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
        self._all_tasks_with_subtasks = None
    
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
            # Get all tasks with subtasks included in the response
            params = {
                "archived": "false",
                "include_closed": "false",
                "subtasks": "true"  # This includes subtask IDs in the response
            }
            response = self.session.get(
                f"{self.config.api_url}/api/v2/list/{self.config.list_id}/task",
                params=params
            )
            response.raise_for_status()
            self._existing_tasks = response.json().get("tasks", [])
            return self._existing_tasks
        except requests.RequestException as e:
            logger.error("Failed to fetch existing tasks", error=str(e))
            return []
    
    def get_all_tasks_with_subtasks(self) -> List[Dict[str, Any]]:
        """Get all tasks including subtasks if configured."""
        if not self.config.check_subtasks:
            return self.get_existing_tickets()
        
        if self._all_tasks_with_subtasks is not None:
            return self._all_tasks_with_subtasks
        
        all_tasks = []
        main_tasks = self.get_existing_tickets()
        all_tasks.extend(main_tasks)
        
        # Collect all subtask IDs from main tasks
        subtask_ids = []
        for task in main_tasks:
            if "subtasks" in task and task["subtasks"]:
                subtask_ids.extend(task["subtasks"])
        
        # Batch fetch subtasks if there are any
        if subtask_ids:
            logger.info(f"Fetching {len(subtask_ids)} subtasks...")
            for subtask_id in subtask_ids[:100]:  # Limit to first 100 to avoid timeout
                try:
                    response = self.session.get(
                        f"{self.config.api_url}/api/v2/task/{subtask_id}"
                    )
                    if response.status_code == 200:
                        subtask_data = response.json()
                        all_tasks.append(subtask_data)
                except requests.RequestException:
                    continue  # Skip failed subtask fetches
        
        self._all_tasks_with_subtasks = all_tasks
        logger.info(f"Fetched {len(all_tasks)} total tasks (including {len(all_tasks) - len(main_tasks)} subtasks)")
        return all_tasks
    
    def _get_subtasks(self, task_id: str, depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively get subtasks for a given task."""
        if depth >= self.config.subtasks_depth:
            return []
        
        try:
            response = self.session.get(
                f"{self.config.api_url}/api/v2/task/{task_id}",
                params={"include_subtasks": "true"}
            )
            response.raise_for_status()
            task_data = response.json()
            
            subtasks = []
            if "subtasks" in task_data:
                for subtask_id in task_data["subtasks"]:
                    # Fetch full subtask data
                    subtask_response = self.session.get(
                        f"{self.config.api_url}/api/v2/task/{subtask_id}"
                    )
                    if subtask_response.status_code == 200:
                        subtask_data = subtask_response.json()
                        subtasks.append(subtask_data)
                        # Recursively get sub-subtasks
                        if depth + 1 < self.config.subtasks_depth:
                            sub_subtasks = self._get_subtasks(subtask_id, depth + 1)
                            subtasks.extend(sub_subtasks)
            
            return subtasks
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch subtasks for task {task_id}: {e}")
            return []
    
    def check_existing(self, alert: Alert) -> Optional[str]:
        """Check if a ticket already exists for this alert."""
        task_name = self._generate_task_name(alert)
        
        # Get all tasks including subtasks if configured
        if self.config.check_subtasks:
            existing_tasks = self.get_all_tasks_with_subtasks()
        else:
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
            "alerte stockage": [r"partition", r"disk.*space"],
            "alerte mémoire": [r"Memory usage", r"RAM"],
            "alerte CPU": [r"CPU usage", r"processor"],
            "alerte systemd service": [r"systemd", r"service.*down"],
            "alerte certificat": [r"certificate.*expire", r"SSL"],
            "backup failed": [r"backup failed", r"backup.*error"],
            "server down": [r"instance.*down", r"server.*unreachable"]
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
        
        # This would integrate with the field mapping system
        # For now, returning empty list
        # TODO: Implement dynamic field mapping
        
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