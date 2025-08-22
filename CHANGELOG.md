# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-XX

### Added
- Initial release
- Grafana alert scraping with multi-source support
- ClickUp integration with dynamic field mapping
- Smart alert processing with rule-based categorization
- Template system for consistent ticket formatting
- Deduplication to prevent duplicate tickets
- Multiple operating modes (dry-run, interactive, batch)
- Rich CLI interface with progress tracking
- Automatic update checking with semver support
- Installation script for easy setup
- Configuration management with YAML
- Caching system for API responses
- Comprehensive logging with structlog

### Features
- `init` command to create configuration
- `test` command to verify connections
- `publish` command with dry-run and interactive modes
- `list-alerts` command to view current alerts
- `list-tickets` command to see existing tickets
- `list-fields` command to discover custom fields
- `version` command with update checking

[Unreleased]: https://github.com/jStrider/grafana-publisher/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jStrider/grafana-publisher/releases/tag/v0.1.0