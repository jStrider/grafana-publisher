"""Doctor command for diagnosing issues."""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import Config
from src.core.logger import get_logger
from src.publishers.clickup import ClickUpPublisher
from src.scrapers.grafana import GrafanaScraper

console = Console()
logger = get_logger(__name__)


class Doctor:
    """System diagnostics and troubleshooting."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def run_diagnostics(self, verbose: bool = False) -> bool:
        """Run all diagnostic checks."""
        console.print("\n[bold cyan]🔍 Running Grafana Publisher Diagnostics[/bold cyan]\n")

        # Installation checks
        self._check_installation()

        # Configuration checks
        self._check_configuration()

        # Environment checks
        self._check_environment()

        # If config is loaded, check connections
        if self.config:
            self._check_connections()
            self._check_permissions()

        # Summary
        self._print_summary()

        return self.checks_failed == 0

    def _check_installation(self):
        """Check installation and paths."""
        console.print("[bold]📦 Installation Checks[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))

        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self._add_success(
                table,
                f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
            )
        else:
            self._add_error(
                table, f"Python {python_version.major}.{python_version.minor} (requires 3.8+)"
            )

        # Check command availability
        commands = ["grafana-publisher", "gpub"]
        for cmd in commands:
            cmd_path = shutil.which(cmd)
            if cmd_path:
                self._add_success(table, f"Command '{cmd}' found at {cmd_path}")
            else:
                self._add_error(table, f"Command '{cmd}' not found in PATH")

        # Check package installation
        try:
            import src

            src_path = Path(src.__file__).parent
            self._add_success(table, f"Package installed at {src_path}")

            # Check if running from source or installed
            if "site-packages" in str(src_path):
                self._add_info(table, "Running from installed package")
            elif ".local/pipx" in str(src_path):
                self._add_info(table, "Installed via pipx")
            else:
                self._add_info(table, "Running from source directory")

        except ImportError:
            self._add_error(table, "Package 'src' not found")

        console.print(table)
        console.print()

    def _check_configuration(self):
        """Check configuration files."""
        console.print("[bold]⚙️  Configuration Checks[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))

        # Check config file locations
        config_paths = [
            Path.home() / ".config" / "grafana-publisher" / "config.yaml",
            Path("config") / "config.yaml",
            Path.cwd() / "config.yaml",
        ]

        config_found = False
        for path in config_paths:
            if path.exists():
                self._add_success(table, f"Config found: {path}")
                config_found = True

                # Check if it's readable
                try:
                    with open(path) as f:
                        f.read(1)
                    self._add_success(table, f"Config readable: {path}")
                except Exception as e:
                    self._add_error(table, f"Cannot read config: {e}")
                break

        if not config_found:
            self._add_error(table, "No configuration file found")
            self._add_info(table, "Run 'grafana-publisher init' to create one")

        # If config is loaded, validate it
        if self.config:
            try:
                # Check required fields
                if self.config.grafana.url:
                    self._add_success(table, f"Grafana URL configured: {self.config.grafana.url}")
                else:
                    self._add_error(table, "Grafana URL not configured")

                # Check publishers
                enabled_publishers = []
                if hasattr(self.config.publishers, "clickup"):
                    clickup_cfg = self.config.publishers.clickup
                    # Check if enabled is explicitly set or if it has configuration
                    if (hasattr(clickup_cfg, "enabled") and clickup_cfg.enabled) or (
                        not hasattr(clickup_cfg, "enabled") and clickup_cfg.token
                    ):
                        enabled_publishers.append("ClickUp")
                if hasattr(self.config.publishers, "jira") and self.config.publishers.jira:
                    if (
                        hasattr(self.config.publishers.jira, "enabled")
                        and self.config.publishers.jira.enabled
                    ):
                        enabled_publishers.append("JIRA")

                if enabled_publishers:
                    self._add_success(table, f"Publishers enabled: {', '.join(enabled_publishers)}")
                else:
                    self._add_warning(table, "No publishers enabled")

            except Exception as e:
                self._add_error(table, f"Config validation error: {e}")

        console.print(table)
        console.print()

    def _check_environment(self):
        """Check environment variables and dependencies."""
        console.print("[bold]🌍 Environment Checks[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))

        # Check for API tokens in environment
        tokens = {
            "GRAFANA_API_TOKEN": "Grafana API Token",
            "CLICKUP_API_TOKEN": "ClickUp API Token",
            "JIRA_API_TOKEN": "JIRA API Token",
        }

        for env_var, name in tokens.items():
            if os.environ.get(env_var):
                self._add_success(table, f"{name} found in environment")
            else:
                self._add_info(table, f"{name} not in environment (may be in config)")

        # Check for required Python packages
        required_packages = [
            "yaml",
            "requests",
            "click",
            "pydantic",
            "structlog",
            "rich",
            "packaging",
        ]

        for package in required_packages:
            try:
                __import__(package)
                self._add_success(table, f"Package '{package}' available")
            except ImportError:
                self._add_error(table, f"Package '{package}' not installed")

        console.print(table)
        console.print()

    def _check_connections(self):
        """Check connections to external services."""
        console.print("[bold]🔌 Connection Checks[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))

        # Test Grafana connection
        try:
            scraper = GrafanaScraper(self.config.grafana)
            if scraper.test_connection():
                self._add_success(table, "Grafana connection successful")

                # Try to fetch alerts
                try:
                    alerts = scraper.fetch_alerts()
                    self._add_info(table, f"Found {len(alerts)} alerts in Grafana")
                except Exception as e:
                    self._add_warning(table, f"Could not fetch alerts: {e}")
            else:
                self._add_error(table, "Grafana connection failed")
        except Exception as e:
            self._add_error(table, f"Grafana connection error: {e}")

        # Test ClickUp connection if enabled
        if hasattr(self.config.publishers, "clickup") and self.config.publishers.clickup.enabled:
            try:
                publisher = ClickUpPublisher(self.config.publishers.clickup)
                if publisher.test_connection():
                    self._add_success(table, "ClickUp connection successful")

                    # Check for existing tasks
                    try:
                        tasks = publisher.get_existing_tickets()
                        self._add_info(table, f"Found {len(tasks)} existing tasks in ClickUp")
                    except Exception as e:
                        self._add_warning(table, f"Could not fetch tasks: {e}")
                else:
                    self._add_error(table, "ClickUp connection failed")
            except Exception as e:
                self._add_error(table, f"ClickUp connection error: {e}")

        console.print(table)
        console.print()

    def _check_permissions(self):
        """Check file and directory permissions."""
        console.print("[bold]🔐 Permission Checks[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))

        # Check config directory
        config_dir = Path.home() / ".config" / "grafana-publisher"
        if config_dir.exists():
            if os.access(config_dir, os.W_OK):
                self._add_success(table, f"Config directory writable: {config_dir}")
            else:
                self._add_warning(table, f"Config directory not writable: {config_dir}")

        # Check log file if configured
        if self.config and hasattr(self.config.settings, "logging"):
            log_file = self.config.settings.logging.file
            if log_file:
                log_path = Path(log_file)
                if log_path.exists():
                    if os.access(log_path, os.W_OK):
                        self._add_success(table, f"Log file writable: {log_path}")
                    else:
                        self._add_error(table, f"Log file not writable: {log_path}")
                else:
                    # Try to create it
                    try:
                        log_path.parent.mkdir(parents=True, exist_ok=True)
                        log_path.touch()
                        self._add_success(table, f"Log file can be created: {log_path}")
                        log_path.unlink()  # Clean up test file
                    except Exception as e:
                        self._add_warning(table, f"Cannot create log file: {e}")

        # Check cache directory if configured
        if self.config:
            try:
                if hasattr(self.config.publishers, "clickup") and hasattr(
                    self.config.publishers.clickup, "cache"
                ):
                    cache_config = self.config.publishers.clickup.cache
                    if cache_config.enabled:
                        cache_path = Path(cache_config.path).expanduser()
                        if cache_path.exists():
                            if os.access(cache_path, os.W_OK):
                                self._add_success(table, f"Cache file writable: {cache_path}")
                            else:
                                self._add_warning(table, f"Cache file not writable: {cache_path}")
            except (AttributeError, TypeError):
                pass  # Config structure might be different

        console.print(table)
        console.print()

    def _add_success(self, table: Table, message: str):
        """Add success message."""
        table.add_row("✅", message)
        self.checks_passed += 1

    def _add_error(self, table: Table, message: str):
        """Add error message."""
        table.add_row("❌", f"[red]{message}[/red]")
        self.checks_failed += 1

    def _add_warning(self, table: Table, message: str):
        """Add warning message."""
        table.add_row("⚠️ ", f"[yellow]{message}[/yellow]")
        self.warnings += 1

    def _add_info(self, table: Table, message: str):
        """Add info message."""
        table.add_row("ℹ️ ", f"[dim]{message}[/dim]")

    def _print_summary(self):
        """Print diagnostic summary."""
        total = self.checks_passed + self.checks_failed

        if self.checks_failed == 0:
            status = "[bold green]✅ All checks passed![/bold green]"
            panel_style = "green"
        elif self.checks_failed < 3:
            status = "[bold yellow]⚠️  Some issues found[/bold yellow]"
            panel_style = "yellow"
        else:
            status = "[bold red]❌ Multiple issues found[/bold red]"
            panel_style = "red"

        summary = f"""
{status}

Checks passed: [green]{self.checks_passed}/{total}[/green]
Warnings: [yellow]{self.warnings}[/yellow]
Errors: [red]{self.checks_failed}[/red]
"""

        if self.checks_failed > 0:
            summary += "\n[dim]Run with -v for more details[/dim]"

        console.print(Panel(summary.strip(), title="Diagnostic Summary", style=panel_style))

        # Provide specific recommendations
        if self.checks_failed > 0:
            console.print("\n[bold]💡 Recommendations:[/bold]")
            recommendations = []

            if "config" in str(self.checks_failed):
                recommendations.append("• Run 'grafana-publisher init' to create configuration")
            if "connection" in str(self.checks_failed):
                recommendations.append("• Check your API tokens and network connectivity")
            if "package" in str(self.checks_failed):
                recommendations.append("• Reinstall with: pip install -e .")

            for rec in recommendations:
                console.print(rec)
