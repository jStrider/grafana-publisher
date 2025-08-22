"""Tests for alert processing."""

import pytest
from src.scrapers.base import Alert


class TestAlert:
    """Test alert functionality."""
    
    def test_alert_creation(self):
        """Test alert object creation."""
        alert = Alert(
            customer_id="test-customer",
            vm="test-vm",
            description="Test alert description",
            severity="high",
            labels={"env": "prod"}
        )
        
        assert alert.customer_id == "test-customer"
        assert alert.vm == "test-vm"
        assert alert.description == "Test alert description"
        assert alert.severity == "high"
        assert alert.labels == {"env": "prod"}
    
    def test_alert_defaults(self):
        """Test alert default values."""
        alert = Alert(
            customer_id="test",
            vm="vm",
            description="desc"
        )
        
        assert alert.severity == "medium"
        assert alert.labels is None
        assert alert.annotations is None
        assert alert.instance is None