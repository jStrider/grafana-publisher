#!/usr/bin/env python3
"""
Grafana Publisher - Main CLI application.

Scrapes Grafana alerts and publishes them to ticketing systems.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import track
from rich.table import Table

from src.core.config import Config
from src.core.logger import get_logger, setup_logging
from src.core.upgrade import check_and_notify_update, perform_upgrade_check
from src.core.version import check_for_updates, format_update_message, get_version
from src.processors.alert_processor import AlertProcessor
from src.publishers.clickup import ClickUpPublisher
from src.scrapers.grafana import GrafanaScraper

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default="config/config.yaml",
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-update-check", is_flag=True, help="Skip automatic update check")
@click.option("--no-auto-upgrade", is_flag=True, help="Disable automatic upgrade (only notify)")
@click.version_option(version=get_version(), prog_name="Grafana Publisher")
@click.pass_context
def cli(ctx, config: Path, verbose: bool, no_update_check: bool, no_auto_upgrade: bool):
    """Grafana Publisher - Scrape alerts and create tickets."""
    ctx.ensure_object(dict)

    # Check for updates and auto-upgrade if possible
    if not no_update_check and ctx.invoked_subcommand not in ["version", "upgrade"]:
        try:
            check_and_notify_update(auto_upgrade=not no_auto_upgrade)
        except Exception:
            pass  # Silently ignore update check failures

    try:
        # Try multiple config locations
        config_paths = [
            config,
            Path.home() / ".config" / "grafana-publisher" / "config.yaml",
            Path("config") / "config.yaml",
        ]

        config_found = None
        for cfg_path in config_paths:
            if cfg_path.exists():
                config_found = cfg_path
                break

        if not config_found:
            console.print("[red]Configuration file not found. Tried:[/red]")
            for cfg_path in config_paths:
                console.print(f"  - {cfg_path}")
            console.print("\n[yellow]Run 'grafana-publisher init' to create a config file[/yellow]")
            sys.exit(1)

        ctx.obj["config"] = Config.from_file(config_found)
        ctx.obj["verbose"] = verbose

        # Setup logging
        log_config = ctx.obj["config"].settings.logging
        setup_logging(
            level="DEBUG" if verbose else log_config.level,
            log_file=log_config.file,
            format_type=log_config.format,
        )

    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def test(ctx):
    """Test connections to Grafana and ticketing systems."""
    config = ctx.obj["config"]

    console.print("\n[bold]Testing connections...[/bold]\n")

    # Test Grafana
    with console.status("Testing Grafana connection..."):
        scraper = GrafanaScraper(config.grafana)
        grafana_ok = scraper.test_connection()

    if grafana_ok:
        console.print("✅ Grafana connection: [green]OK[/green]")
    else:
        console.print("❌ Grafana connection: [red]FAILED[/red]")

    # Test publishers
    for name, pub_config in config.publishers.items():
        if not pub_config.enabled:
            continue

        with console.status(f"Testing {name} connection..."):
            if name == "clickup":
                publisher = ClickUpPublisher(pub_config)
                pub_ok = publisher.test_connection()

        if pub_ok:
            console.print(f"✅ {name.capitalize()} connection: [green]OK[/green]")
        else:
            console.print(f"❌ {name.capitalize()} connection: [red]FAILED[/red]")

    console.print()


@cli.command()
@click.option(
    "--dry-run", "-d", is_flag=True, help="Show what would be created without creating tickets"
)
@click.option("--interactive", "-i", is_flag=True, help="Confirm each ticket before creation")
@click.option(
    "--publisher",
    "-p",
    type=click.Choice(["clickup", "jira"]),
    default="clickup",
    help="Publisher to use",
)
@click.pass_context
def publish(ctx, dry_run: bool, interactive: bool, publisher: str):
    """Fetch alerts and publish to ticketing system."""
    config = ctx.obj["config"]

    # Get publisher config
    pub_config = config.get_publisher(publisher)
    if not pub_config or not pub_config.enabled:
        console.print(f"[red]Publisher '{publisher}' is not enabled[/red]")
        return

    # Initialize components
    scraper = GrafanaScraper(config.grafana)
    processor = AlertProcessor(config)

    if publisher == "clickup":
        pub = ClickUpPublisher(pub_config)
    else:
        console.print(f"[red]Publisher '{publisher}' not implemented yet[/red]")
        return

    # Fetch alerts
    with console.status("Fetching alerts from Grafana..."):
        alerts = scraper.fetch_alerts()

    if not alerts:
        console.print("[yellow]No alerts found[/yellow]")
        return

    console.print(f"\n[bold]Found {len(alerts)} alerts[/bold]\n")

    # Process alerts
    processed_alerts = processor.process_alerts(alerts)

    # Statistics
    created = 0
    skipped = 0
    failed = 0

    # Create table for results
    table = Table(title="Publishing Results")
    table.add_column("Alert", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Publish each alert
    for processed in track(processed_alerts, description="Publishing alerts..."):
        alert = processed["alert"]
        alert_name = f"[{alert.customer_id}][{alert.vm}]"

        if interactive and not dry_run:
            console.print(f"\n[bold]Alert:[/bold] {alert_name}")
            console.print(f"[bold]Description:[/bold] {alert.description[:100]}...")
            if not click.confirm("Create ticket?"):
                table.add_row(alert_name, "[yellow]SKIPPED[/yellow]", "User skipped")
                skipped += 1
                continue

        result = pub.publish(alert, dry_run=dry_run)

        if result.success:
            if dry_run:
                table.add_row(alert_name, "[cyan]WOULD CREATE[/cyan]", result.skipped_reason or "")
            else:
                table.add_row(alert_name, "[green]CREATED[/green]", result.ticket_url or "")
            created += 1
        elif result.skipped:
            table.add_row(alert_name, "[yellow]EXISTS[/yellow]", result.skipped_reason or "")
            skipped += 1
        else:
            table.add_row(alert_name, "[red]FAILED[/red]", result.error or "")
            failed += 1

    # Display results
    console.print("\n")
    console.print(table)

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if dry_run:
        console.print(f"  Would create: [green]{created}[/green]")
    else:
        console.print(f"  Created: [green]{created}[/green]")
    console.print(f"  Skipped: [yellow]{skipped}[/yellow]")
    console.print(f"  Failed: [red]{failed}[/red]")


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_alerts(ctx, format: str):
    """List current alerts from Grafana."""
    config = ctx.obj["config"]

    scraper = GrafanaScraper(config.grafana)

    with console.status("Fetching alerts..."):
        alerts = scraper.fetch_alerts()

    if not alerts:
        console.print("[yellow]No alerts found[/yellow]")
        return

    if format == "table":
        table = Table(title=f"Grafana Alerts ({len(alerts)} total)")
        table.add_column("Customer", style="cyan")
        table.add_column("VM", style="magenta")
        table.add_column("Description")
        table.add_column("Severity", style="yellow")

        for alert in alerts:
            severity_color = {
                "critical": "[red]",
                "high": "[yellow]",
                "medium": "[blue]",
                "low": "[green]",
            }.get(alert.severity.lower(), "")

            description = (
                alert.description[:50] + "..." if len(alert.description) > 50 else alert.description
            )
            table.add_row(
                alert.customer_id,
                alert.vm,
                description,
                f"{severity_color}{alert.severity}[/{severity_color.strip('[]')}]",
            )

        console.print(table)

    elif format == "json":
        import json

        data = [alert.to_dict() for alert in alerts]
        console.print(json.dumps(data, indent=2))

    elif format == "yaml":
        import yaml

        data = [alert.to_dict() for alert in alerts]
        console.print(yaml.dump(data, default_flow_style=False))


@cli.command()
@click.option(
    "--publisher",
    "-p",
    type=click.Choice(["clickup", "jira"]),
    default="clickup",
    help="Publisher to check",
)
@click.pass_context
def list_tickets(ctx, publisher: str):
    """List existing tickets in the ticketing system."""
    config = ctx.obj["config"]

    pub_config = config.get_publisher(publisher)
    if not pub_config or not pub_config.enabled:
        console.print(f"[red]Publisher '{publisher}' is not enabled[/red]")
        return

    if publisher == "clickup":
        pub = ClickUpPublisher(pub_config)
    else:
        console.print(f"[red]Publisher '{publisher}' not implemented yet[/red]")
        return

    with console.status("Fetching existing tickets..."):
        tickets = pub.get_existing_tickets()

    if not tickets:
        console.print("[yellow]No tickets found[/yellow]")
        return

    table = Table(title=f"Existing Tickets ({len(tickets)} total)")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Status", style="yellow")
    table.add_column("URL")

    for ticket in tickets[:50]:  # Limit to 50 for display
        table.add_row(
            ticket.get("id", ""),
            ticket.get("name", "")[:60],
            ticket.get("status", {}).get("status", ""),
            f"https://app.clickup.com/t/{ticket.get('id', '')}",
        )

    console.print(table)

    if len(tickets) > 50:
        console.print(f"\n[yellow]Showing first 50 of {len(tickets)} tickets[/yellow]")


@cli.command()
@click.option(
    "--publisher",
    "-p",
    type=click.Choice(["clickup", "jira"]),
    default="clickup",
    help="Publisher to check fields for",
)
@click.pass_context
def list_fields(ctx, publisher: str):
    """List available custom fields in the ticketing system."""
    config = ctx.obj["config"]

    pub_config = config.get_publisher(publisher)
    if not pub_config or not pub_config.enabled:
        console.print(f"[red]Publisher '{publisher}' is not enabled[/red]")
        return

    if publisher == "clickup":
        pub = ClickUpPublisher(pub_config)
        fields = pub.get_field_definitions()
    else:
        console.print(f"[red]Publisher '{publisher}' not implemented yet[/red]")
        return

    if not fields:
        console.print("[yellow]No custom fields found[/yellow]")
        return

    table = Table(title="Custom Fields")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type", style="yellow")
    table.add_column("Options")

    for field in fields:
        field_type = field.get("type", "")
        options = ""

        if field_type in ["drop_down", "labels"]:
            opts = field.get("type_config", {}).get("options", [])
            key = "label" if field_type == "labels" else "name"
            opt_names = [opt.get(key, "") for opt in opts[:3]]
            options = ", ".join(opt_names)
            if len(opts) > 3:
                options += f" (+{len(opts) - 3} more)"

        table.add_row(field.get("id", ""), field.get("name", ""), field_type, options)

    console.print(table)


@cli.command()
def init():
    """Initialize configuration file."""
    config_dir = Path.home() / ".config" / "grafana-publisher"
    config_file = config_dir / "config.yaml"
    example_file = Path(__file__).parent / "config" / "config.example.yaml"

    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)

    if config_file.exists():
        if not click.confirm(f"Config file already exists at {config_file}. Overwrite?"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

    # Copy example config
    if example_file.exists():
        import shutil

        shutil.copy(example_file, config_file)
        console.print(f"[green]✓ Configuration created at {config_file}[/green]")
    else:
        # Create minimal config
        minimal_config = """# Grafana Publisher Configuration
grafana:
  url: "https://monitoring.example.com"
  token: "${GRAFANA_API_TOKEN}"
  sources:
    - name: "production"
      folder_id: "your_folder_id"
      rules_group: "Alerts"
      labels_filter:
        notification: "infra"

publishers:
  clickup:
    enabled: true
    api_url: "https://api.clickup.com"
    token: "${CLICKUP_API_TOKEN}"
    list_id: "your_list_id"
    field_mappings: {}
    cache:
      enabled: true
      ttl: 86400

alert_rules: []
templates: {}

settings:
  deduplication:
    enabled: true
    strategy: "task_name"
  modes:
    dry_run: false
    interactive: false
  output:
    format: "rich"
  logging:
    level: "INFO"
    file: "grafana_publisher.log"
    format: "json"
"""
        with open(config_file, "w") as f:
            f.write(minimal_config)
        console.print(f"[green]✓ Configuration created at {config_file}[/green]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Edit the configuration file:")
    console.print(f"   nano {config_file}")
    console.print("\n2. Set your API tokens:")
    console.print("   export GRAFANA_API_TOKEN='your_token'")
    console.print("   export CLICKUP_API_TOKEN='your_token'")
    console.print("\n3. Test the connection:")
    console.print("   grafana-publisher test")


@cli.command()
@click.option("--check", is_flag=True, help="Check for updates")
def version(check):
    """Show version information."""
    console.print(f"[bold]Grafana Publisher[/bold] version {get_version()}")

    if check:
        with console.status("Checking for updates..."):
            update_info = check_for_updates(force=True)

        if update_info:
            if update_info[2]:
                console.print(format_update_message(update_info[0], update_info[1]))
            else:
                console.print("[green]✓ You are running the latest version[/green]")
        else:
            console.print("[yellow]Could not check for updates[/yellow]")


@cli.command()
@click.option("--auto", is_flag=True, help="Automatically upgrade without prompting")
@click.option("--check", is_flag=True, help="Only check for updates without upgrading")
def upgrade(auto, check):
    """Check for updates and upgrade Grafana Publisher."""
    if check:
        # Just check, don't upgrade
        perform_upgrade_check(auto_upgrade=False, interactive=False)
    else:
        # Try to upgrade
        result = perform_upgrade_check(auto_upgrade=auto, interactive=not auto)
        
        if result is None:
            console.print("[green]✓ Already on the latest version[/green]")
        elif result:
            console.print("[green]✅ Upgrade successful! Please restart the application.[/green]")
            sys.exit(0)
        else:
            console.print("[yellow]Upgrade was not completed.[/yellow]")
            sys.exit(1)


if __name__ == "__main__":
    cli()
