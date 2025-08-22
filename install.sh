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
VENV_DIR="$HOME/.local/share/grafana-publisher/venv"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Grafana Publisher Installation        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
fi

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo "  Install with: brew install python3"
    fi
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

if ! command_exists git; then
    echo -e "${RED}✗ git is not installed${NC}"
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo "  Install with: brew install git"
    fi
    exit 1
fi
echo -e "${GREEN}✓ git found${NC}"

# Check for pipx (preferred on macOS)
if [[ "$OS_TYPE" == "macos" ]] && command_exists pipx; then
    echo -e "${GREEN}✓ pipx found (recommended for macOS)${NC}"
    USE_PIPX=true
else
    USE_PIPX=false
fi

# Installation method selection
echo ""
echo -e "${YELLOW}Select installation method:${NC}"

if [[ "$OS_TYPE" == "macos" ]]; then
    if [[ "$USE_PIPX" == "true" ]]; then
        echo "1) Install with pipx (recommended for macOS)"
        echo "2) Install with virtual environment"
        echo "3) Install from current directory (development)"
        read -p "Choice [1-3]: " INSTALL_METHOD
    else
        echo "1) Install with virtual environment (recommended)"
        echo "2) Install from current directory (development)"
        echo "3) Install with pipx (requires: brew install pipx)"
        read -p "Choice [1-3]: " INSTALL_METHOD
        
        # Adjust choice numbers if pipx is not available
        if [[ "$INSTALL_METHOD" == "3" ]]; then
            echo -e "${YELLOW}Installing pipx first...${NC}"
            if command_exists brew; then
                brew install pipx
                pipx ensurepath
                export PATH="$HOME/.local/bin:$PATH"
                USE_PIPX=true
                INSTALL_METHOD="1"
            else
                echo -e "${RED}Homebrew not found. Please install pipx manually.${NC}"
                exit 1
            fi
        elif [[ "$INSTALL_METHOD" == "2" ]]; then
            INSTALL_METHOD="3"  # Map to development install
        fi
    fi
else
    echo "1) Install from GitHub (recommended)"
    echo "2) Install from current directory (development)"
    echo "3) Install with pip (when published to PyPI)"
    read -p "Choice [1-3]: " INSTALL_METHOD
fi

# Handle installation based on OS and method
if [[ "$OS_TYPE" == "macos" ]]; then
    case $INSTALL_METHOD in
        1)
            if [[ "$USE_PIPX" == "true" ]]; then
                echo -e "${BLUE}Installing with pipx...${NC}"
                
                # Check if we're in the project directory
                if [ -f "setup.py" ]; then
                    INSTALL_PATH="."
                else
                    # Clone from GitHub
                    TEMP_DIR=$(mktemp -d)
                    cd "$TEMP_DIR"
                    echo -e "${YELLOW}Cloning repository...${NC}"
                    git clone "$REPO_URL" grafana-publisher
                    INSTALL_PATH="./grafana-publisher"
                fi
                
                echo -e "${YELLOW}Installing package with pipx...${NC}"
                pipx install "$INSTALL_PATH"
                
                # Copy config files  
                mkdir -p "$CONFIG_DIR"
                if [ -f "$INSTALL_PATH/config/config.example.yaml" ]; then
                    [ ! -f "$CONFIG_DIR/config.yaml" ] && cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.yaml"
                    cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.example.yaml"
                fi
                
                # Cleanup if we cloned
                if [ -n "$TEMP_DIR" ]; then
                    cd /
                    rm -rf "$TEMP_DIR"
                fi
            else
                # Virtual environment installation
                echo -e "${BLUE}Installing with virtual environment...${NC}"
                
                # Create venv directory
                mkdir -p "$(dirname "$VENV_DIR")"
                
                # Create virtual environment
                echo -e "${YELLOW}Creating virtual environment...${NC}"
                python3 -m venv "$VENV_DIR"
                
                # Activate and install
                source "$VENV_DIR/bin/activate"
                
                if [ -f "setup.py" ]; then
                    echo -e "${YELLOW}Installing from current directory...${NC}"
                    pip install -e .
                    INSTALL_PATH="."
                else
                    # Clone and install
                    TEMP_DIR=$(mktemp -d)
                    cd "$TEMP_DIR"
                    echo -e "${YELLOW}Cloning repository...${NC}"
                    git clone "$REPO_URL" grafana-publisher
                    cd grafana-publisher
                    pip install -e .
                    INSTALL_PATH="."
                fi
                
                # Create wrapper script
                mkdir -p "$INSTALL_DIR"
                cat > "$INSTALL_DIR/grafana-publisher" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/grafana-publisher/venv/bin/activate"
exec python -m src.cli "$@"
EOF
                chmod +x "$INSTALL_DIR/grafana-publisher"
                ln -sf "$INSTALL_DIR/grafana-publisher" "$INSTALL_DIR/gp"
                
                # Copy config files
                mkdir -p "$CONFIG_DIR"
                [ ! -f "$CONFIG_DIR/config.yaml" ] && cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.yaml"
                cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.example.yaml"
                
                # Cleanup
                if [ -n "$TEMP_DIR" ]; then
                    cd /
                    rm -rf "$TEMP_DIR"
                fi
                
                deactivate
            fi
            ;;
        
        2|3)
            echo -e "${BLUE}Installing from current directory (development)...${NC}"
            
            if [ ! -f "setup.py" ]; then
                echo -e "${RED}✗ setup.py not found. Please run from grafana-publisher directory${NC}"
                exit 1
            fi
            
            # Create virtual environment for development
            echo -e "${YELLOW}Creating development virtual environment...${NC}"
            python3 -m venv venv
            source venv/bin/activate
            
            echo -e "${YELLOW}Installing package in development mode...${NC}"
            pip install -e ".[dev]"
            
            # Create wrapper script
            mkdir -p "$INSTALL_DIR"
            CURRENT_DIR=$(pwd)
            cat > "$INSTALL_DIR/grafana-publisher" << EOF
#!/bin/bash
source "$CURRENT_DIR/venv/bin/activate"
exec python "$CURRENT_DIR/main.py" "\$@"
EOF
            chmod +x "$INSTALL_DIR/grafana-publisher"
            ln -sf "$INSTALL_DIR/grafana-publisher" "$INSTALL_DIR/gp"
            
            # Copy config files
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            
            deactivate
            ;;
        
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
else
    # Linux installation (original logic)
    case $INSTALL_METHOD in
        1)
            echo -e "${BLUE}Installing from GitHub...${NC}"
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            git clone "$REPO_URL" grafana-publisher
            cd grafana-publisher
            pip3 install --user -e .
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            cd /
            rm -rf "$TEMP_DIR"
            ;;
        
        2)
            echo -e "${BLUE}Installing from current directory...${NC}"
            if [ ! -f "setup.py" ]; then
                echo -e "${RED}✗ setup.py not found${NC}"
                exit 1
            fi
            pip3 install --user -e .
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            ;;
        
        3)
            echo -e "${BLUE}Installing from PyPI...${NC}"
            pip3 install --user grafana-publisher
            mkdir -p "$CONFIG_DIR"
            ;;
        
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
fi

# Verify installation
echo ""
echo -e "${YELLOW}Verifying installation...${NC}"

if command_exists grafana-publisher; then
    echo -e "${GREEN}✓ grafana-publisher command is available${NC}"
elif [ -f "$INSTALL_DIR/grafana-publisher" ]; then
    echo -e "${GREEN}✓ grafana-publisher installed at $INSTALL_DIR${NC}"
elif command_exists pipx && pipx list | grep -q grafana-publisher; then
    echo -e "${GREEN}✓ grafana-publisher installed with pipx${NC}"
else
    echo -e "${YELLOW}⚠ Installation complete but command may not be in PATH${NC}"
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

if [ -f "$CONFIG_DIR/config.yaml" ]; then
    echo -e "${GREEN}✓ Configuration file ready at:${NC}"
    echo "  $CONFIG_DIR/config.yaml"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT - Update your configuration:${NC}"
    echo ""
    echo -e "${BLUE}1. Edit the configuration file:${NC}"
    echo "   nano $CONFIG_DIR/config.yaml"
    echo ""
    echo "   Key values to update:"
    echo "   • grafana.url → Your Grafana URL"
    echo "   • grafana.sources[0].folder_id → Your folder ID"
    echo "   • publishers.clickup.list_id → Your ClickUp list ID"
    echo ""
    echo -e "${BLUE}2. Set your API tokens:${NC}"
    echo "   export GRAFANA_API_TOKEN='your_token'"
    echo "   export CLICKUP_API_TOKEN='your_token'"
    echo ""
    echo "   Or add them directly in config.yaml (less secure)"
else
    echo -e "${RED}✗ Configuration file was not created${NC}"
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

# Skip update check on first install since we just installed

echo -e "${GREEN}Happy monitoring! 🚀${NC}"