"""Auto-upgrade functionality for Grafana Publisher."""

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from src.core.logger import get_logger
from src.core.version import check_for_updates, get_version, parse_version

logger = get_logger(__name__)


class InstallMethod(Enum):
    """Installation method detection."""
    
    PIP = "pip"
    PIPX = "pipx"
    UV = "uv"
    HOMEBREW = "homebrew"
    GITHUB_RELEASE = "github"
    DEVELOPMENT = "development"
    UNKNOWN = "unknown"


def detect_installation_method() -> InstallMethod:
    """
    Detect how Grafana Publisher was installed.
    
    Returns:
        InstallMethod enum indicating the installation method
    """
    # Check if running from development (git repo with .git directory)
    current_dir = Path(__file__).parent.parent.parent
    if (current_dir / ".git").exists():
        logger.debug("Detected development installation (git repository)")
        return InstallMethod.DEVELOPMENT
    
    # Check if installed via Homebrew
    try:
        result = subprocess.run(
            ["brew", "list", "grafana-publisher"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.debug("Detected Homebrew installation")
            return InstallMethod.HOMEBREW
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Check if installed via uv
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "grafana-publisher" in result.stdout:
            logger.debug("Detected uv installation")
            return InstallMethod.UV
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Check if installed via pipx
    try:
        result = subprocess.run(
            ["pipx", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "grafana-publisher" in result.stdout:
            logger.debug("Detected pipx installation")
            return InstallMethod.PIPX
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Check if installed via pip
    try:
        import pkg_resources
        try:
            pkg_resources.get_distribution("grafana-publisher")
            logger.debug("Detected pip installation")
            return InstallMethod.PIP
        except pkg_resources.DistributionNotFound:
            pass
    except ImportError:
        pass
    
    # Check for GitHub release binary
    if getattr(sys, 'frozen', False):
        # Running as compiled binary
        logger.debug("Detected GitHub release binary")
        return InstallMethod.GITHUB_RELEASE
    
    logger.debug("Could not detect installation method")
    return InstallMethod.UNKNOWN


def attempt_auto_upgrade(install_method: InstallMethod, target_version: str) -> tuple[bool, str]:
    """
    Attempt to automatically upgrade Grafana Publisher.
    
    Args:
        install_method: Detected installation method
        target_version: Target version to upgrade to
        
    Returns:
        Tuple of (success, message)
    """
    # Clean version string
    if target_version.startswith("v"):
        target_version = target_version[1:]
    
    logger.info(f"Attempting auto-upgrade to version {target_version} via {install_method.value}")
    
    if install_method == InstallMethod.PIP:
        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "grafana-publisher"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f"Successfully upgraded to version {target_version}"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"pip upgrade failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Upgrade timed out"
        except Exception as e:
            return False, f"Upgrade error: {str(e)}"
    
    elif install_method == InstallMethod.UV:
        try:
            cmd = ["uv", "tool", "upgrade", "grafana-publisher"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f"Successfully upgraded to version {target_version}"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"uv upgrade failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Upgrade timed out"
        except Exception as e:
            return False, f"Upgrade error: {str(e)}"
    
    elif install_method == InstallMethod.PIPX:
        try:
            cmd = ["pipx", "upgrade", "grafana-publisher"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f"Successfully upgraded to version {target_version}"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"pipx upgrade failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Upgrade timed out"
        except Exception as e:
            return False, f"Upgrade error: {str(e)}"
    
    elif install_method == InstallMethod.HOMEBREW:
        try:
            # First update Homebrew
            subprocess.run(["brew", "update"], capture_output=True, timeout=30)
            
            # Then upgrade the package
            cmd = ["brew", "upgrade", "grafana-publisher"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f"Successfully upgraded to version {target_version}"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"Homebrew upgrade failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Upgrade timed out"
        except Exception as e:
            return False, f"Upgrade error: {str(e)}"
    
    elif install_method == InstallMethod.DEVELOPMENT:
        try:
            # Find the git repository root
            current_dir = Path(__file__).parent.parent.parent
            
            # Check if there are uncommitted changes
            status_cmd = ["git", "-C", str(current_dir), "status", "--porcelain"]
            status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
            
            if status_result.stdout.strip():
                # There are uncommitted changes
                logger.warning("Uncommitted changes detected, cannot auto-update")
                return False, "Uncommitted changes detected. Please commit or stash your changes first"
            
            # Get current branch
            branch_cmd = ["git", "-C", str(current_dir), "rev-parse", "--abbrev-ref", "HEAD"]
            branch_result = subprocess.run(branch_cmd, capture_output=True, text=True, timeout=10)
            current_branch = branch_result.stdout.strip()
            
            # For version updates, we should check main branch for releases
            # But pull from current branch for development
            update_branch = "main" if current_branch != "main" else current_branch
            
            # Fetch latest changes from both branches
            logger.info(f"Fetching latest changes from origin")
            fetch_cmd = ["git", "-C", str(current_dir), "fetch", "origin"]
            fetch_result = subprocess.run(fetch_cmd, capture_output=True, text=True, timeout=30)
            
            if fetch_result.returncode != 0:
                return False, f"Failed to fetch updates: {fetch_result.stderr}"
            
            # Check if there's a new version tag on main
            if current_branch != "main":
                # Check if main has new version tags
                tags_cmd = ["git", "-C", str(current_dir), "tag", "--merged", "origin/main", "--sort=-version:refname"]
                tags_result = subprocess.run(tags_cmd, capture_output=True, text=True, timeout=10)
                
                if tags_result.returncode == 0 and tags_result.stdout.strip():
                    latest_tag = tags_result.stdout.strip().split('\n')[0]
                    # Check if we should switch to main for the latest release
                    logger.info(f"Latest release tag on main: {latest_tag}")
                    
                    # For now, just pull current branch updates
                    # In production, users should use released versions from main
            
            # Check if we're behind on current branch
            behind_cmd = ["git", "-C", str(current_dir), "rev-list", "--count", f"HEAD..origin/{current_branch}"]
            behind_result = subprocess.run(behind_cmd, capture_output=True, text=True, timeout=10)
            commits_behind = int(behind_result.stdout.strip() or "0")
            
            if commits_behind == 0:
                # If on develop, check if main has updates
                if current_branch == "develop":
                    main_behind_cmd = ["git", "-C", str(current_dir), "rev-list", "--count", "HEAD..origin/main"]
                    main_behind_result = subprocess.run(main_behind_cmd, capture_output=True, text=True, timeout=10)
                    main_commits_behind = int(main_behind_result.stdout.strip() or "0")
                    
                    if main_commits_behind > 0:
                        return False, f"New release available on main branch. Switch to main branch and pull to get the latest stable version"
                
                return True, "Already up to date with the repository"
            
            # Pull the changes from current branch
            logger.info(f"Pulling {commits_behind} commits from origin/{current_branch}")
            pull_cmd = ["git", "-C", str(current_dir), "pull", "origin", current_branch]
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=30)
            
            if pull_result.returncode == 0:
                # Check if requirements changed
                requirements_file = current_dir / "requirements.txt"
                if requirements_file.exists():
                    # Update dependencies
                    logger.info("Updating dependencies...")
                    pip_cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "-q"]
                    subprocess.run(pip_cmd, capture_output=True, timeout=60)
                
                return True, f"Successfully pulled {commits_behind} commits from origin/{current_branch}"
            else:
                error_msg = pull_result.stderr.strip() if pull_result.stderr else "Unknown error"
                return False, f"Git pull failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Git operation timed out"
        except Exception as e:
            return False, f"Git update error: {str(e)}"
    
    elif install_method == InstallMethod.GITHUB_RELEASE:
        return False, "Binary installation - please download the latest release from GitHub"
    
    else:
        return False, "Unknown installation method"


def get_upgrade_command(install_method: InstallMethod) -> str:
    """
    Get the manual upgrade command for the detected installation method.
    
    Args:
        install_method: Detected installation method
        
    Returns:
        String with the upgrade command
    """
    commands = {
        InstallMethod.PIP: "pip install --upgrade grafana-publisher",
        InstallMethod.UV: "uv tool upgrade grafana-publisher",
        InstallMethod.PIPX: "pipx upgrade grafana-publisher",
        InstallMethod.HOMEBREW: "brew upgrade grafana-publisher",
        InstallMethod.DEVELOPMENT: "git pull origin main",
        InstallMethod.GITHUB_RELEASE: "Download from: https://github.com/jStrider/grafana-publisher/releases/latest",
        InstallMethod.UNKNOWN: "pip install --upgrade grafana-publisher"
    }
    
    return commands.get(install_method, "pip install --upgrade grafana-publisher")


def perform_upgrade_check(auto_upgrade: bool = False, interactive: bool = True) -> Optional[bool]:
    """
    Check for updates and optionally perform auto-upgrade.
    
    Args:
        auto_upgrade: Whether to attempt automatic upgrade
        interactive: Whether to prompt user for upgrade
        
    Returns:
        True if upgraded, False if not upgraded, None if no update available
    """
    from rich.console import Console
    from rich.prompt import Confirm
    
    console = Console()
    
    # Check for updates
    update_info = check_for_updates(force=True)
    
    if not update_info:
        logger.debug("Could not check for updates")
        return None
    
    latest_version, release_url, is_newer = update_info
    
    if not is_newer:
        logger.debug(f"Already on latest version: {get_version()}")
        return None
    
    # Detect installation method
    install_method = detect_installation_method()
    
    console.print(f"\n[yellow]📦 New version available: {latest_version} (current: {get_version()})[/yellow]")
    console.print(f"[dim]Release notes: {release_url}[/dim]\n")
    
    # Attempt auto-upgrade if requested
    if auto_upgrade:
        console.print(f"[cyan]Attempting automatic upgrade via {install_method.value}...[/cyan]")
        success, message = attempt_auto_upgrade(install_method, latest_version)
        
        if success:
            console.print(f"[green]✅ {message}[/green]")
            console.print("[yellow]Please restart the application to use the new version.[/yellow]")
            return True
        else:
            console.print(f"[red]❌ Auto-upgrade failed: {message}[/red]")
            
            # Provide manual upgrade command
            upgrade_cmd = get_upgrade_command(install_method)
            console.print(f"\n[yellow]To upgrade manually, run:[/yellow]")
            console.print(f"[cyan]  {upgrade_cmd}[/cyan]\n")
            
            if interactive and install_method != InstallMethod.DEVELOPMENT:
                # Ask if user wants to try manual upgrade now
                if Confirm.ask("Would you like to try the upgrade command now?"):
                    console.print(f"[cyan]Running: {upgrade_cmd}[/cyan]")
                    
                    if install_method in [InstallMethod.PIP, InstallMethod.PIPX, InstallMethod.HOMEBREW]:
                        try:
                            # Execute the upgrade command
                            if install_method == InstallMethod.PIP:
                                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "grafana-publisher"]
                            elif install_method == InstallMethod.PIPX:
                                cmd = ["pipx", "upgrade", "grafana-publisher"]
                            else:  # Homebrew
                                cmd = ["brew", "upgrade", "grafana-publisher"]
                            
                            result = subprocess.run(cmd, timeout=60)
                            
                            if result.returncode == 0:
                                console.print("[green]✅ Upgrade completed! Please restart the application.[/green]")
                                return True
                            else:
                                console.print("[red]❌ Upgrade failed. Please try manually.[/red]")
                                return False
                                
                        except Exception as e:
                            console.print(f"[red]❌ Error running upgrade: {e}[/red]")
                            return False
            
            return False
    
    else:
        # Just show upgrade information
        upgrade_cmd = get_upgrade_command(install_method)
        console.print(f"[yellow]Installation method: {install_method.value}[/yellow]")
        console.print(f"[cyan]To upgrade, run: {upgrade_cmd}[/cyan]\n")
        
        if interactive and install_method != InstallMethod.DEVELOPMENT:
            if Confirm.ask("Would you like to upgrade now?"):
                return perform_upgrade_check(auto_upgrade=True, interactive=False)
        
        return False


def check_and_notify_update(auto_upgrade: bool = True) -> None:
    """
    Check for updates and optionally auto-upgrade (non-blocking).
    Used during normal CLI operations.
    
    Args:
        auto_upgrade: Whether to attempt automatic upgrade (default: True)
    """
    update_info = check_for_updates()
    
    if update_info:
        latest_version, release_url, is_newer = update_info
        
        if is_newer:
            from rich.console import Console
            console = Console()
            
            install_method = detect_installation_method()
            
            if auto_upgrade:
                # Try automatic upgrade silently
                console.print(f"[dim]📦 New version {latest_version} available, attempting auto-upgrade...[/dim]")
                success, message = attempt_auto_upgrade(install_method, latest_version)
                
                if success:
                    console.print(f"[green]✅ Auto-upgraded to {latest_version}! Restarting...[/green]")
                    # Restart the application with the same arguments
                    import os
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    # If auto-upgrade fails, show manual instructions
                    upgrade_cmd = get_upgrade_command(install_method)
                    
                    # Only show error details for development mode or if it's not a simple "not supported" message
                    if install_method == InstallMethod.DEVELOPMENT and "Uncommitted changes" in message:
                        console.print(f"[yellow]⚠️  {message}[/yellow]")
                    
                    console.print(f"[yellow]📦 Update available: {latest_version} (current: {get_version()})[/yellow]")
                    console.print(f"[cyan]Run 'grafana-publisher upgrade' or: {upgrade_cmd}[/cyan]")
                    console.print(f"[dim]Release notes: {release_url}[/dim]\n")
            else:
                # Just notify without auto-upgrade
                upgrade_cmd = get_upgrade_command(install_method)
                console.print(f"[yellow]📦 Update available: {latest_version} (current: {get_version()})[/yellow]")
                console.print(f"[cyan]Run 'grafana-publisher upgrade' or: {upgrade_cmd}[/cyan]")
                console.print(f"[dim]Release notes: {release_url}[/dim]\n")