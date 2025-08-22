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

# Function to detect if we're in a git repository
in_git_repo() {
    git rev-parse --git-dir > /dev/null 2>&1
}

# Function to get current git branch
get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main"
}

# Check if we're running from within the repository
if [ -f "pyproject.toml" ] && [ -d "src" ] && in_git_repo; then
    IN_REPO=true
    CURRENT_BRANCH=$(get_current_branch)
    echo -e "${GREEN}Running from repository (branch: $CURRENT_BRANCH)${NC}"
else
    IN_REPO=false
fi

# Detect OS
OS="$(uname -s)"

echo ""
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if command_exists python3; then
    echo -e "${GREEN}✓ Python 3 found${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3 first"
    exit 1
fi

# Check git
if command_exists git; then
    echo -e "${GREEN}✓ git found${NC}"
else
    echo -e "${RED}✗ git not found${NC}"
    echo "Please install git first"
    exit 1
fi

# Check for pipx on macOS
USE_PIPX=false
if [[ "$OS" == "Darwin" ]]; then
    if command_exists pipx; then
        echo -e "${GREEN}✓ pipx found (recommended for macOS)${NC}"
        USE_PIPX=true
    else
        echo -e "${YELLOW}! pipx not found (recommended for macOS)${NC}"
        echo "  Install with: brew install pipx"
    fi
fi

echo ""
echo -e "${YELLOW}Select installation method:${NC}"

# Different options based on context and OS
if $IN_REPO; then
    # Running from within repo
    echo "1) Install from current directory (development mode)"
    echo "2) Install with pipx (isolated environment)"
    echo "3) Install with virtual environment"
    read -p "Choice [1-3]: " INSTALL_METHOD
    
    case $INSTALL_METHOD in
        1)
            echo -e "${BLUE}Installing from current directory...${NC}"
            if command_exists pipx && $USE_PIPX; then
                pipx install -e .
            else
                pip3 install --user -e .
            fi
            
            # Copy config
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            ;;
            
        2)
            echo -e "${BLUE}Installing with pipx...${NC}"
            if ! command_exists pipx; then
                echo -e "${YELLOW}Installing pipx first...${NC}"
                if [[ "$OS" == "Darwin" ]] && command_exists brew; then
                    brew install pipx
                    pipx ensurepath
                else
                    python3 -m pip install --user pipx
                    python3 -m pipx ensurepath
                fi
            fi
            pipx install .
            
            # Copy config
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            ;;
            
        3)
            echo -e "${BLUE}Installing with virtual environment...${NC}"
            
            # Create venv
            python3 -m venv "$VENV_DIR"
            source "$VENV_DIR/bin/activate"
            pip install -e .
            
            # Create wrapper script
            mkdir -p "$INSTALL_DIR"
            cat > "$INSTALL_DIR/grafana-publisher" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
exec python -m src.main_cli "\$@"
EOF
            chmod +x "$INSTALL_DIR/grafana-publisher"
            
            # Create gpub alias
            ln -sf "$INSTALL_DIR/grafana-publisher" "$INSTALL_DIR/gpub"
            
            # Copy config
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            ;;
            
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
elif [[ "$OS" == "Darwin" ]] && $USE_PIPX; then
    # macOS with pipx available
    echo "1) Install with pipx (recommended)"
    echo "2) Install with virtual environment"
    read -p "Choice [1-2]: " INSTALL_METHOD
    
    case $INSTALL_METHOD in
        1)
            echo -e "${BLUE}Installing with pipx...${NC}"
            
            # Clone from GitHub (main branch for stable)
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            echo -e "${YELLOW}Cloning repository...${NC}"
            git clone "$REPO_URL" grafana-publisher
            cd grafana-publisher
            
            # Check latest version tag and checkout
            LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
            if [ -n "$LATEST_TAG" ]; then
                echo -e "${YELLOW}Using latest release: $LATEST_TAG${NC}"
                git checkout "$LATEST_TAG"
            else
                echo -e "${YELLOW}Using main branch${NC}"
                git checkout main
            fi
            
            pipx install .
            
            # Copy config files  
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            
            # Cleanup
            cd /
            rm -rf "$TEMP_DIR"
            ;;
            
        2)
            echo -e "${BLUE}Installing with virtual environment...${NC}"
            
            # Clone from GitHub
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            echo -e "${YELLOW}Cloning repository...${NC}"
            git clone "$REPO_URL" grafana-publisher
            cd grafana-publisher
            
            # Check latest version tag
            LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
            if [ -n "$LATEST_TAG" ]; then
                echo -e "${YELLOW}Using latest release: $LATEST_TAG${NC}"
                git checkout "$LATEST_TAG"
            else
                echo -e "${YELLOW}Using main branch${NC}"
                git checkout main
            fi
            
            # Create venv
            python3 -m venv "$VENV_DIR"
            source "$VENV_DIR/bin/activate"
            pip install .
            
            # Create wrapper script
            mkdir -p "$INSTALL_DIR"
            cat > "$INSTALL_DIR/grafana-publisher" << 'EOF'
#!/bin/bash
source "$HOME/.local/share/grafana-publisher/venv/bin/activate"
exec python -m src.main_cli "$@"
EOF
            chmod +x "$INSTALL_DIR/grafana-publisher"
            
            # Create gpub alias
            ln -sf "$INSTALL_DIR/grafana-publisher" "$INSTALL_DIR/gpub"
            
            # Copy config
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            
            # Cleanup
            cd /
            rm -rf "$TEMP_DIR"
            ;;
            
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
else
    # Linux or macOS without pipx
    echo "1) Install from GitHub (latest release)"
    echo "2) Install from GitHub (development version)"
    read -p "Choice [1-2]: " INSTALL_METHOD
    
    case $INSTALL_METHOD in
        1)
            echo -e "${BLUE}Installing latest release...${NC}"
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            
            echo -e "${YELLOW}Cloning repository...${NC}"
            git clone "$REPO_URL" grafana-publisher
            cd grafana-publisher
            
            # Check latest version tag and checkout
            LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
            if [ -n "$LATEST_TAG" ]; then
                echo -e "${YELLOW}Using latest release: $LATEST_TAG${NC}"
                git checkout "$LATEST_TAG"
            else
                echo -e "${YELLOW}Using main branch${NC}"
                git checkout main
            fi
            
            pip3 install --user .
            
            # Copy config
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            
            cd /
            rm -rf "$TEMP_DIR"
            ;;
            
        2)
            echo -e "${BLUE}Installing development version...${NC}"
            TEMP_DIR=$(mktemp -d)
            cd "$TEMP_DIR"
            
            echo -e "${YELLOW}Cloning repository (develop branch)...${NC}"
            git clone -b develop "$REPO_URL" grafana-publisher
            cd grafana-publisher
            
            pip3 install --user -e .
            
            # Copy config
            mkdir -p "$CONFIG_DIR"
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
            cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
            
            cd /
            rm -rf "$TEMP_DIR"
            ;;
            
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
fi

# Add to PATH if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "${YELLOW}Adding $INSTALL_DIR to PATH...${NC}"
    
    # Detect shell
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
    export PATH="$PATH:$INSTALL_DIR"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation Complete!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Grafana Publisher has been installed successfully!${NC}"
echo ""
echo "Configuration file: $CONFIG_DIR/config.yaml"
echo ""
echo "Next steps:"
echo "1. Edit the configuration file:"
echo "   ${BLUE}nano $CONFIG_DIR/config.yaml${NC}"
echo ""
echo "2. Add your Grafana and ClickUp/Jira credentials"
echo ""
echo "3. Test the connection:"
echo "   ${BLUE}grafana-publisher test${NC}"
echo ""
echo "Usage:"
echo "   ${BLUE}grafana-publisher --help${NC}"
echo "   ${BLUE}gpub --help${NC} (short alias)"
echo ""

# Check if grafana-publisher is available
if command_exists grafana-publisher || command_exists gpub; then
    echo -e "${GREEN}✓ Command 'grafana-publisher' is available${NC}"
else
    echo -e "${YELLOW}! You may need to restart your terminal or run:${NC}"
    echo "  ${BLUE}source $SHELL_RC${NC}"
fi