"""Base publisher interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.scrapers.base import Alert


class PublishResult:
    """Result of publishing operation."""
    
    def __init__(
        self,
        success: bool,
        ticket_id: Optional[str] = None,
        ticket_url: Optional[str] = None,
        error: Optional[str] = None,
        skipped: bool = False,
        skipped_reason: Optional[str] = None
    ):
        self.success = success
        self.ticket_id = ticket_id
        self.ticket_url = ticket_url
        self.error = error
        self.skipped = skipped
        self.skipped_reason = skipped_reason
    
    def __repr__(self) -> str:
        if self.success:
            return f"PublishResult(success=True, ticket_id={self.ticket_id})"
        elif self.skipped:
            return f"PublishResult(skipped=True, reason={self.skipped_reason})"
        else:
            return f"PublishResult(success=False, error={self.error})"


class BasePublisher(ABC):
    """Base class for all publishers."""
    
    @abstractmethod
    def publish(self, alert: Alert, dry_run: bool = False) -> PublishResult:
        """
        Publish an alert to the ticketing system.
        
        Args:
            alert: Alert to publish
            dry_run: If True, simulate publishing without creating ticket
            
        Returns:
            PublishResult object
        """
        pass
    
    @abstractmethod
    def check_existing(self, alert: Alert) -> Optional[str]:
        """
        Check if a ticket already exists for this alert.
        
        Args:
            alert: Alert to check
            
        Returns:
            Ticket ID if exists, None otherwise
        """
        pass
    
    @abstractmethod
    def get_existing_tickets(self) -> List[Dict[str, Any]]:
        """
        Get list of existing tickets.
        
        Returns:
            List of ticket dictionaries
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the ticketing system.
        
        Returns:
            True if connection successful
        """
        pass