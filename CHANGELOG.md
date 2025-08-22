# [0.2.0](https://github.com/jStrider/grafana-publisher/compare/v0.1.0...v0.2.0) (2025-08-22)


### Bug Fixes

* add package-lock.json for CI/CD ([dccfe24](https://github.com/jStrider/grafana-publisher/commit/dccfe247b9af29eeb1ae8fb21c6e404d44ebc945))
* resolve CI/CD pipeline issues ([691e538](https://github.com/jStrider/grafana-publisher/commit/691e538328ff64642d4e855806b36ed9505c0f17))
* resolve ClickUp API 400 errors ([ab040bf](https://github.com/jStrider/grafana-publisher/commit/ab040bfeab076e74097955523ed53f66c31b7dfb))
* resolve linting issues and code formatting ([c4dbd6a](https://github.com/jStrider/grafana-publisher/commit/c4dbd6a11a90d39800af00c8622caf7ec1d577c5))
* use full functional ClickUp URLs instead of broken short ones ([33ffc3f](https://github.com/jStrider/grafana-publisher/commit/33ffc3f7517a49071930dde3b481c8ddfd3e1586))


### Features

* add doctor command for system diagnostics ([a0cada4](https://github.com/jStrider/grafana-publisher/commit/a0cada4f3b1a5b0812e8f2957818a30749d7d730))
* add semantic-release and CI/CD pipelines ([6a9458a](https://github.com/jStrider/grafana-publisher/commit/6a9458afbceaea94b249600dea1cbc8579c760ef))
* display ClickUp URLs instead of IDs in publish output ([9437149](https://github.com/jStrider/grafana-publisher/commit/943714993710b5b3a1225ed0e8bcc5cfe48881d1))
* improve ClickUp integration with required fields ([69e50f4](https://github.com/jStrider/grafana-publisher/commit/69e50f4f031b4a16ea0bcad526b7cf3c7c352690))

# [0.2.0-develop.2](https://github.com/jStrider/grafana-publisher/compare/v0.2.0-develop.1...v0.2.0-develop.2) (2025-08-22)


### Bug Fixes

* resolve CI/CD pipeline issues ([691e538](https://github.com/jStrider/grafana-publisher/commit/691e538328ff64642d4e855806b36ed9505c0f17))

# [0.2.0-develop.1](https://github.com/jStrider/grafana-publisher/compare/v0.1.0...v0.2.0-develop.1) (2025-08-22)


### Bug Fixes

* add package-lock.json for CI/CD ([dccfe24](https://github.com/jStrider/grafana-publisher/commit/dccfe247b9af29eeb1ae8fb21c6e404d44ebc945))
* resolve ClickUp API 400 errors ([ab040bf](https://github.com/jStrider/grafana-publisher/commit/ab040bfeab076e74097955523ed53f66c31b7dfb))
* resolve linting issues and code formatting ([c4dbd6a](https://github.com/jStrider/grafana-publisher/commit/c4dbd6a11a90d39800af00c8622caf7ec1d577c5))
* use full functional ClickUp URLs instead of broken short ones ([33ffc3f](https://github.com/jStrider/grafana-publisher/commit/33ffc3f7517a49071930dde3b481c8ddfd3e1586))


### Features

* add doctor command for system diagnostics ([a0cada4](https://github.com/jStrider/grafana-publisher/commit/a0cada4f3b1a5b0812e8f2957818a30749d7d730))
* add semantic-release and CI/CD pipelines ([6a9458a](https://github.com/jStrider/grafana-publisher/commit/6a9458afbceaea94b249600dea1cbc8579c760ef))
* display ClickUp URLs instead of IDs in publish output ([9437149](https://github.com/jStrider/grafana-publisher/commit/943714993710b5b3a1225ed0e8bcc5cfe48881d1))
* improve ClickUp integration with required fields ([69e50f4](https://github.com/jStrider/grafana-publisher/commit/69e50f4f031b4a16ea0bcad526b7cf3c7c352690))

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
