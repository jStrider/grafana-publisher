"""Version management and update checking."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import requests
from packaging import version

from src.core.logger import get_logger

logger = get_logger(__name__)

# Current version - single source of truth
__version__ = "0.1.0"

# GitHub repository information
GITHUB_OWNER = "jStrider"
GITHUB_REPO = "grafana-publisher"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Version check cache
VERSION_CACHE_FILE = Path.home() / ".grafana_publisher_version_cache.json"
VERSION_CHECK_INTERVAL = timedelta(hours=24)


def get_version() -> str:
    """Get the current version."""
    return __version__


def parse_version(version_string: str) -> version.Version:
    """
    Parse a version string.

    Args:
        version_string: Version string (e.g., "1.2.3", "v1.2.3")

    Returns:
        Parsed version object
    """
    # Remove 'v' prefix if present
    if version_string.startswith("v"):
        version_string = version_string[1:]

    return version.parse(version_string)


def should_check_for_updates() -> bool:
    """
    Determine if we should check for updates.

    Returns:
        True if update check is needed
    """
    if not VERSION_CACHE_FILE.exists():
        return True

    try:
        with open(VERSION_CACHE_FILE) as f:
            cache = json.load(f)

        last_check = datetime.fromisoformat(cache.get("last_check", "2000-01-01"))
        return datetime.now() - last_check > VERSION_CHECK_INTERVAL

    except (json.JSONDecodeError, ValueError):
        return True


def save_version_cache(latest_version: str, release_url: str) -> None:
    """
    Save version check cache.

    Args:
        latest_version: Latest version found
        release_url: URL to the release
    """
    cache = {
        "last_check": datetime.now().isoformat(),
        "latest_version": latest_version,
        "release_url": release_url,
    }

    VERSION_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERSION_CACHE_FILE, "w") as f:
        json.dump(cache, f)


def get_cached_version_info() -> Optional[Tuple[str, str]]:
    """
    Get cached version information.

    Returns:
        Tuple of (latest_version, release_url) or None
    """
    if not VERSION_CACHE_FILE.exists():
        return None

    try:
        with open(VERSION_CACHE_FILE) as f:
            cache = json.load(f)

        return cache.get("latest_version"), cache.get("release_url")

    except (json.JSONDecodeError, KeyError):
        return None


def check_for_updates(force: bool = False) -> Optional[Tuple[str, str, bool]]:
    """
    Check for available updates.

    Args:
        force: Force check even if recently checked

    Returns:
        Tuple of (latest_version, release_url, is_newer) or None if check fails
    """
    # Use cache if available and not forcing
    if not force and not should_check_for_updates():
        cached = get_cached_version_info()
        if cached:
            latest_version, release_url = cached
            try:
                is_newer = parse_version(latest_version) > parse_version(__version__)
                return latest_version, release_url, is_newer
            except Exception:
                pass

    # Fetch latest release from GitHub
    try:
        response = requests.get(
            GITHUB_API_URL, headers={"Accept": "application/vnd.github.v3+json"}, timeout=5
        )

        if response.status_code == 404:
            # Repository or releases not found
            logger.debug("No releases found on GitHub")
            return None

        response.raise_for_status()
        data = response.json()

        latest_version = data.get("tag_name", "")
        release_url = data.get("html_url", "")

        if not latest_version:
            return None

        # Save to cache
        save_version_cache(latest_version, release_url)

        # Compare versions
        current = parse_version(__version__)
        latest = parse_version(latest_version)
        is_newer = latest > current

        logger.debug(
            f"Version check: current={__version__}, latest={latest_version}, newer={is_newer}"
        )

        return latest_version, release_url, is_newer

    except requests.RequestException as e:
        logger.debug(f"Failed to check for updates: {e}")
        # Try to use cached version if available
        cached = get_cached_version_info()
        if cached:
            latest_version, release_url = cached
            try:
                is_newer = parse_version(latest_version) > parse_version(__version__)
                return latest_version, release_url, is_newer
            except Exception:
                pass
        return None
    except Exception as e:
        logger.debug(f"Error checking for updates: {e}")
        return None


def format_update_message(latest_version: str, release_url: str) -> str:
    """
    Format update available message.

    Args:
        latest_version: Latest version available
        release_url: URL to the release

    Returns:
        Formatted message
    """
    return (
        f"\n📦 A new version is available: {latest_version} (current: {__version__})\n"
        f"   Update with: pip install --upgrade grafana-publisher\n"
        f"   Release notes: {release_url}\n"
    )
