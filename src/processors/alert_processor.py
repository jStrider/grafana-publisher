"""Alert processing and filtering."""

import re
from typing import Optional

from src.core.config import AlertRule, Config
from src.core.logger import get_logger
from src.scrapers.base import Alert

logger = get_logger(__name__)


class AlertProcessor:
    """Processes and filters alerts based on rules."""

    def __init__(self, config: Config):
        """
        Initialize alert processor.

        Args:
            config: Application configuration
        """
        self.config = config
        self.alert_rules = config.alert_rules
        self.templates = config.templates

    def process_alerts(self, alerts: list[Alert]) -> list[dict]:
        """
        Process list of alerts.

        Args:
            alerts: List of raw alerts

        Returns:
            List of processed alert dictionaries
        """
        processed = []

        for alert in alerts:
            processed_alert = self.process_alert(alert)
            if processed_alert:
                processed.append(processed_alert)

        logger.info(f"Processed {len(processed)} out of {len(alerts)} alerts")
        return processed

    def process_alert(self, alert: Alert) -> Optional[dict]:
        """
        Process a single alert.

        Args:
            alert: Alert to process

        Returns:
            Processed alert dictionary or None if filtered out
        """
        # Find matching rule
        rule = self._find_matching_rule(alert)

        if not rule:
            # No rule matched, use default processing
            return self._default_process(alert)

        # Apply rule
        processed = {
            "alert": alert,
            "rule": rule.name,
            "priority": rule.priority,
            "template": rule.template,
            "fields": rule.fields,
        }

        # Apply template if exists
        if rule.template in self.templates:
            template = self.templates[rule.template]
            processed["title"] = self._format_template(template.title, alert)
            processed["description"] = self._format_template(template.description, alert)

        return processed

    def _find_matching_rule(self, alert: Alert) -> Optional[AlertRule]:
        """
        Find the first matching rule for an alert.

        Args:
            alert: Alert to match

        Returns:
            Matching AlertRule or None
        """
        for rule in self.alert_rules:
            if self._matches_rule(alert, rule):
                logger.debug("Alert matched rule", rule=rule.name, alert=alert.customer_id)
                return rule

        return None

    def _matches_rule(self, alert: Alert, rule: AlertRule) -> bool:
        """
        Check if alert matches a rule.

        Args:
            alert: Alert to check
            rule: Rule to match against

        Returns:
            True if alert matches rule
        """
        description = alert.description

        for pattern in rule.patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return True

        return False

    def _default_process(self, alert: Alert) -> dict:
        """
        Default processing for alerts without matching rules.

        Args:
            alert: Alert to process

        Returns:
            Processed alert dictionary
        """
        return {
            "alert": alert,
            "rule": "default",
            "priority": "medium",
            "template": None,
            "fields": {},
            "title": f"[{alert.customer_id}][{alert.vm}]",
            "description": alert.description,
        }

    def _format_template(self, template: str, alert: Alert) -> str:
        """
        Format template string with alert data.

        Args:
            template: Template string
            alert: Alert object

        Returns:
            Formatted string
        """
        import datetime

        context = {
            "customer_id": alert.customer_id,
            "vm": alert.vm,
            "description": alert.description,
            "severity": alert.severity,
            "instance": alert.instance or "",
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Add labels and annotations to context
        for key, value in alert.labels.items():
            context[f"label_{key}"] = value

        for key, value in alert.annotations.items():
            context[f"annotation_{key}"] = value

        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning("Template formatting error", error=str(e), template=template[:50])
            return template
