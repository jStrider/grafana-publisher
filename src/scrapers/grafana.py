"""Grafana alert scraper."""

from typing import Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import GrafanaConfig, GrafanaSource
from src.core.logger import get_logger
from src.scrapers.base import Alert, BaseScraper

logger = get_logger(__name__)


class GrafanaScraper(BaseScraper):
    """Scraper for Grafana alerts."""

    ALERTS_ENDPOINT = "/api/alertmanager/grafana/api/v2/alerts/groups"

    def __init__(self, config: GrafanaConfig):
        """
        Initialize Grafana scraper.

        Args:
            config: Grafana configuration
        """
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic."""
        session = requests.Session()

        # Setup retry strategy
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers
        session.headers.update(
            {"Authorization": f"Bearer {self.config.token}", "Content-Type": "application/json"}
        )

        # SSL verification
        session.verify = self.config.verify_ssl

        return session

    def test_connection(self) -> bool:
        """Test connection to Grafana API."""
        try:
            response = self.session.get(
                f"{self.config.url}/api/health", timeout=self.config.timeout
            )
            response.raise_for_status()
            logger.info("Grafana connection successful", url=self.config.url)
            return True
        except requests.RequestException as e:
            logger.error("Grafana connection failed", url=self.config.url, error=str(e))
            return False

    def fetch_alerts(self) -> List[Alert]:
        """Fetch alerts from Grafana."""
        all_alerts = []

        for source in self.config.sources:
            alerts = self._fetch_source_alerts(source)
            all_alerts.extend(alerts)

        logger.info(f"Fetched {len(all_alerts)} alerts from Grafana")
        return all_alerts

    def _fetch_source_alerts(self, source: GrafanaSource) -> List[Alert]:
        """
        Fetch alerts from a specific source.

        Args:
            source: Grafana source configuration

        Returns:
            List of alerts from this source
        """
        try:
            response = self.session.get(
                f"{self.config.url}{self.ALERTS_ENDPOINT}", timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_alerts(data, source)

        except requests.RequestException as e:
            logger.error("Failed to fetch alerts from source", source=source.name, error=str(e))
            return []

    def _parse_alerts(self, data: Dict, source: GrafanaSource) -> List[Alert]:
        """
        Parse alerts from Grafana response.

        Args:
            data: Grafana API response
            source: Source configuration

        Returns:
            List of parsed alerts
        """
        alerts = []

        for group in data:
            for alert_data in group.get("alerts", []):
                # Check if alert matches source filters
                if not self._matches_filters(alert_data, source):
                    continue

                # Extract alert information
                labels = alert_data.get("labels", {})
                annotations = alert_data.get("annotations", {})

                # Try to extract customer_id and vm from labels or instance
                customer_id = labels.get("customer_id")
                vm = labels.get("vm")
                instance = labels.get("instance", "")

                # Fallback: extract from instance if not in labels
                if not customer_id or not vm:
                    if instance and "." in instance:
                        parts = instance.split(".")
                        if not vm:
                            vm = parts[0]
                        if not customer_id and len(parts) > 1:
                            customer_id = parts[1]

                # Skip if we don't have essential information
                if not customer_id or not vm:
                    logger.debug(
                        "Skipping alert without customer_id or vm", labels=labels, instance=instance
                    )
                    continue

                alert = Alert(
                    customer_id=customer_id,
                    vm=vm,
                    description=annotations.get("description", "No description"),
                    severity=labels.get("severity", "medium"),
                    labels=labels,
                    annotations=annotations,
                    instance=instance,
                )

                alerts.append(alert)

        return alerts

    def _matches_filters(self, alert_data: Dict, source: GrafanaSource) -> bool:
        """
        Check if alert matches source filters.

        Args:
            alert_data: Alert data from Grafana
            source: Source configuration

        Returns:
            True if alert matches filters
        """
        if not source.labels_filter:
            return True

        labels = alert_data.get("labels", {})

        for key, value in source.labels_filter.items():
            if labels.get(key) != value:
                return False

        return True
