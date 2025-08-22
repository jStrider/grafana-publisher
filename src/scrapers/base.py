"""Base scraper interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Alert:
    """Represents an alert."""
    
    def __init__(
        self,
        customer_id: str,
        vm: str,
        description: str,
        severity: str = "medium",
        labels: Dict[str, str] = None,
        annotations: Dict[str, str] = None,
        instance: str = None
    ):
        self.customer_id = customer_id
        self.vm = vm
        self.description = description
        self.severity = severity
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.instance = instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "customer_id": self.customer_id,
            "vm": self.vm,
            "description": self.description,
            "severity": self.severity,
            "labels": self.labels,
            "annotations": self.annotations,
            "instance": self.instance
        }
    
    def __repr__(self) -> str:
        return f"Alert(customer_id={self.customer_id}, vm={self.vm}, description={self.description[:50]}...)"


class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    @abstractmethod
    def fetch_alerts(self) -> List[Alert]:
        """
        Fetch alerts from the monitoring system.
        
        Returns:
            List of Alert objects
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the monitoring system.
        
        Returns:
            True if connection successful
        """
        pass