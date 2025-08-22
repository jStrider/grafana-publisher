# Grafana Publisher

A flexible and extensible tool for scraping Grafana alerts and automatically creating tickets in various ticketing systems (ClickUp, Jira, etc.).

## Features

- **Multi-source Grafana scraping**: Support for multiple alert sources with label filtering
- **Extensible publisher system**: Easy to add new ticketing systems
- **Dynamic field mapping**: Automatic field discovery and mapping with caching
- **Smart alert processing**: Rule-based alert categorization and templating
- **Deduplication**: Prevents duplicate ticket creation
- **Multiple operating modes**: Interactive, dry-run, and batch modes
- **Rich CLI interface**: Beautiful output with progress tracking

## Installation

### Quick Install (Recommended)

```bash
# Download and run the installer
curl -sSL https://raw.githubusercontent.com/jStrider/grafana-publisher/main/install.sh | bash
```

### Manual Installation

#### From GitHub
```bash
# Clone the repository
git clone https://github.com/jStrider/grafana-publisher.git
cd grafana-publisher

# Install with pip
pip install -e .

# Or use the install script
./install.sh
```

#### From PyPI (when available)
```bash
pip install grafana-publisher
```

### Development Installation
```bash
# Clone and install with dev dependencies
git clone https://github.com/jStrider/grafana-publisher.git
cd grafana-publisher
make install-dev
```

## Getting Started

### 1. Initialize Configuration

```bash
# Create config file
grafana-publisher init

# Or manually copy the example
cp ~/.config/grafana-publisher/config.example.yaml ~/.config/grafana-publisher/config.yaml
```

### 2. Configure Your Settings

Edit `~/.config/grafana-publisher/config.yaml`:

```yaml
grafana:
  url: "https://monitoring.example.com"
  token: "${GRAFANA_API_TOKEN}"  # Set in environment or .env file
  
publishers:
  clickup:
    enabled: true
    api_url: "https://api.clickup.com"
    token: "${CLICKUP_API_TOKEN}"
    list_id: "your_list_id"
```

### 3. Set API Tokens
```bash
# Option 1: Environment variables
export GRAFANA_API_TOKEN="your_grafana_token"
export CLICKUP_API_TOKEN="your_clickup_token"

# Option 2: .env file
echo "GRAFANA_API_TOKEN=your_grafana_token" >> .env
echo "CLICKUP_API_TOKEN=your_clickup_token" >> .env
```

## Usage

### Test connections
```bash
grafana-publisher test
# or use short alias
gp test
```

### Check version and updates
```bash
grafana-publisher version
grafana-publisher version --check
```

### List current alerts
```bash
grafana-publisher list-alerts
grafana-publisher list-alerts --format json
```

### Publish alerts (dry-run)
```bash
grafana-publisher publish --dry-run
gp publish -d  # short version
```

### Publish alerts (interactive mode)
```bash
grafana-publisher publish --interactive
gp publish -i  # short version
```

### Publish alerts (batch mode)
```bash
grafana-publisher publish
```

### List existing tickets
```bash
grafana-publisher list-tickets
```

### List available custom fields
```bash
grafana-publisher list-fields --publisher clickup
```

### Skip update checks
```bash
grafana-publisher --no-update-check publish
```

## Alert Rules

Configure alert processing rules in `config.yaml`:

```yaml
alert_rules:
  - name: "disk_space"
    patterns:
      - "partition.*"
      - "disk.*space"
    priority: "high"
    template: "storage_alert"
    fields:
      support_type: "storage"
```

## Templates

Define ticket templates for consistent formatting:

```yaml
templates:
  storage_alert:
    title: "[{customer_id}][{vm}] Storage Alert"
    description: |
      **Alert**: Storage issue detected
      **Customer**: {customer_id}
      **VM**: {vm}
      **Details**: {description}
      **Time**: {timestamp}
```

## Architecture

```
grafana-publisher/
├── src/
│   ├── core/           # Core functionality
│   │   ├── config.py   # Configuration management
│   │   ├── cache.py    # Caching system
│   │   └── logger.py   # Logging
│   ├── scrapers/       # Alert scrapers
│   │   ├── base.py     # Base scraper interface
│   │   └── grafana.py  # Grafana implementation
│   ├── publishers/     # Ticket publishers
│   │   ├── base.py     # Base publisher interface
│   │   └── clickup.py  # ClickUp implementation
│   └── processors/     # Alert processing
│       ├── alert_processor.py  # Rule-based processing
│       └── field_mapper.py     # Dynamic field mapping
└── main.py             # CLI application
```

## Adding a New Publisher

To add support for a new ticketing system:

1. Create a new publisher class in `src/publishers/`:
```python
from src.publishers.base import BasePublisher, PublishResult

class MyPublisher(BasePublisher):
    def publish(self, alert, dry_run=False):
        # Implementation
        pass
    
    def check_existing(self, alert):
        # Implementation
        pass
```

2. Add configuration in `config.yaml`:
```yaml
publishers:
  my_system:
    enabled: true
    api_url: "https://api.mysystem.com"
    token: "${MY_SYSTEM_TOKEN}"
```

3. Register in `main.py`:
```python
if publisher == "my_system":
    pub = MyPublisher(pub_config)
```

## Version Management

The project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Automatic Update Checking
The tool automatically checks for updates once per day and notifies you when a new version is available.

### Version Commands
```bash
# Show current version
grafana-publisher version

# Check for updates manually
grafana-publisher version --check

# Disable automatic update checks
grafana-publisher --no-update-check [command]
```

### Making a Release (Maintainers)
```bash
# Bump version
make version-patch  # 0.1.0 -> 0.1.1
make version-minor  # 0.1.0 -> 0.2.0
make version-major  # 0.1.0 -> 1.0.0

# Create release
make release
git push origin v0.1.1
```

## Development

### Setup Development Environment
```bash
make install-dev
```

### Run tests
```bash
make test
```

### Format and lint code
```bash
make format
make lint
```

### Build distribution
```bash
make build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details