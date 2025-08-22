#!/usr/bin/env python3
"""
Grafana Publisher - CLI entry point.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for development mode
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import cli as app_cli


def main():
    """Main entry point for installed package."""
    app_cli()


if __name__ == "__main__":
    main()