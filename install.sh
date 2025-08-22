#!/bin/bash

###############################################################################
#                     Grafana Publisher Installation Script                   #
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/grafana-publisher"
REPO_URL="https://github.com/jStrider/grafana-publisher.git"
SCRIPT_NAME="grafana-publisher"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Grafana Publisher Installation        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

if ! command_exists pip3; then
    echo -e "${RED}✗ pip3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip3 found${NC}"

if ! command_exists git; then
    echo -e "${RED}✗ git is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ git found${NC}"

# Installation method selection
echo ""
echo -e "${YELLOW}Select installation method:${NC}"
echo "1) Install from GitHub (recommended)"
echo "2) Install from current directory (development)"
echo "3) Install with pip (when published to PyPI)"
read -p "Choice [1-3]: " INSTALL_METHOD

case $INSTALL_METHOD in
    1)
        echo -e "${BLUE}Installing from GitHub...${NC}"
        
        # Create temp directory
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        # Clone repository
        echo -e "${YELLOW}Cloning repository...${NC}"
        git clone "$REPO_URL" grafana-publisher
        cd grafana-publisher
        
        # Install with pip
        echo -e "${YELLOW}Installing package...${NC}"
        pip3 install --user -e .
        
        # Copy config example
        mkdir -p "$CONFIG_DIR"
        cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
        
        # Cleanup
        cd /
        rm -rf "$TEMP_DIR"
        ;;
    
    2)
        echo -e "${BLUE}Installing from current directory...${NC}"
        
        # Check if we're in the right directory
        if [ ! -f "setup.py" ]; then
            echo -e "${RED}✗ setup.py not found. Please run from grafana-publisher directory${NC}"
            exit 1
        fi
        
        # Install with pip
        echo -e "${YELLOW}Installing package...${NC}"
        pip3 install --user -e .
        
        # Copy config example
        mkdir -p "$CONFIG_DIR"
        cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
        ;;
    
    3)
        echo -e "${BLUE}Installing from PyPI...${NC}"
        echo -e "${YELLOW}Installing package...${NC}"
        pip3 install --user grafana-publisher
        
        # Create config directory
        mkdir -p "$CONFIG_DIR"
        ;;
    
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Create symbolic link for easy access
echo -e "${YELLOW}Creating command shortcut...${NC}"
mkdir -p "$INSTALL_DIR"

# Check if grafana-publisher command is available
if command_exists grafana-publisher; then
    echo -e "${GREEN}✓ grafana-publisher command installed${NC}"
else
    # Try to find the installed script
    SCRIPT_PATH=$(python3 -c "import site; print(site.USER_BASE)")/bin/grafana-publisher
    if [ -f "$SCRIPT_PATH" ]; then
        ln -sf "$SCRIPT_PATH" "$INSTALL_DIR/grafana-publisher"
        ln -sf "$SCRIPT_PATH" "$INSTALL_DIR/gp"
        echo -e "${GREEN}✓ Created shortcuts: grafana-publisher and gp${NC}"
    fi
fi

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}Adding $HOME/.local/bin to PATH...${NC}"
    
    # Detect shell
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    echo -e "${GREEN}✓ Added to $SHELL_RC${NC}"
    echo -e "${YELLOW}  Run 'source $SHELL_RC' to update current session${NC}"
fi

# Configuration setup
echo ""
echo -e "${YELLOW}Setting up configuration...${NC}"

if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    if [ -f "$CONFIG_DIR/config.example.yaml" ]; then
        echo -e "${BLUE}Example configuration created at:${NC}"
        echo "  $CONFIG_DIR/config.example.yaml"
        echo ""
        echo -e "${YELLOW}To complete setup:${NC}"
        echo "1. Copy the example config:"
        echo "   cp $CONFIG_DIR/config.example.yaml $CONFIG_DIR/config.yaml"
        echo ""
        echo "2. Edit the config with your settings:"
        echo "   nano $CONFIG_DIR/config.yaml"
        echo ""
        echo "3. Set your API tokens in environment or .env file:"
        echo "   export GRAFANA_API_TOKEN='your_token'"
        echo "   export CLICKUP_API_TOKEN='your_token'"
    fi
else
    echo -e "${GREEN}✓ Configuration already exists${NC}"
fi

# Final message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Installation Complete!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo "  grafana-publisher --help      # Show help"
echo "  grafana-publisher test        # Test connections"
echo "  grafana-publisher publish -d  # Dry run"
echo "  gp publish                    # Short command"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure your API tokens"
echo "2. Edit $CONFIG_DIR/config.yaml"
echo "3. Run 'grafana-publisher test' to verify setup"
echo ""

# Check for updates on first install
echo -e "${YELLOW}Checking for updates...${NC}"
python3 -c "
try:
    from src.core.version import check_for_updates, format_update_message
    result = check_for_updates()
    if result and result[2]:
        print(format_update_message(result[0], result[1]))
except:
    pass
" 2>/dev/null || true

echo -e "${GREEN}Happy monitoring! 🚀${NC}"