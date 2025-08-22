"""Base scraper interface."""

from abc import ABC, abstractmethod
from typing import Any


class Alert:
    """Represents an alert."""

    def __init__(
        self,
        customer_id: str,
        vm: str,
        description: str,
        severity: str = "medium",
        labels: dict[str, str] = None,
        annotations: dict[str, str] = None,
        instance: str = None,
    ):
        self.customer_id = customer_id
        self.vm = vm
        self.description = description
        self.severity = severity
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.instance = instance

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "customer_id": self.customer_id,
            "vm": self.vm,
            "description": self.description,
            "severity": self.severity,
            "labels": self.labels,
            "annotations": self.annotations,
            "instance": self.instance,
        }

    def __repr__(self) -> str:
        description_preview = self.description[:50]
        return (
            f"Alert(customer_id={self.customer_id}, vm={self.vm}, "
            f"description={description_preview}...)"
        )


class BaseScraper(ABC):
    """Base class for all scrapers."""

    @abstractmethod
    def fetch_alerts(self) -> list[Alert]:
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
