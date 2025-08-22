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

# Function to check if we're in a git repository
in_git_repo() {
    git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Function to get current git branch
get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# Function to get latest git tag
get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo ""
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

# Check for uv (most preferred)
if command_exists uv; then
    echo -e "${GREEN}✓ uv found (recommended package manager)${NC}"
    USE_UV=true
else
    USE_UV=false
fi

# Check for pipx (preferred on macOS if uv not available)
if command_exists pipx; then
    echo -e "${GREEN}✓ pipx found${NC}"
    USE_PIPX=true
else
    USE_PIPX=false
fi

# Determine if we're running from the repository
IN_REPO=false
if [ -f "pyproject.toml" ] && [ -d "src" ] && in_git_repo; then
    IN_REPO=true
    CURRENT_BRANCH=$(get_current_branch)
    echo -e "${GREEN}Running from repository (branch: $CURRENT_BRANCH)${NC}"
fi

# Function to get the best version/branch to install
get_install_source() {
    if [[ "$IN_REPO" == "true" ]]; then
        # Use current directory
        echo "."
    else
        # Clone from GitHub and try to use latest stable tag
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        echo -e "${YELLOW}Cloning repository...${NC}"
        git clone "$REPO_URL" grafana-publisher
        cd grafana-publisher
        
        # Try to checkout latest stable tag
        LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        if [[ -n "$LATEST_TAG" ]] && [[ ! "$LATEST_TAG" =~ -develop\. ]]; then
            echo -e "${GREEN}Using latest stable release: $LATEST_TAG${NC}"
            git checkout "$LATEST_TAG" >/dev/null 2>&1
        else
            echo -e "${YELLOW}Using main branch${NC}"
            git checkout main >/dev/null 2>&1 || true
        fi
        
        echo "$TEMP_DIR/grafana-publisher"
    fi
}

# Installation method selection
echo ""
echo -e "${YELLOW}Select installation method:${NC}"

if [[ "$OS_TYPE" == "macos" ]]; then
    # Build menu based on available tools
    MENU_OPTIONS=()
    MENU_MAP=()
    
    option_num=1
    
    # Add uv option if available
    if [[ "$USE_UV" == "true" ]]; then
        MENU_OPTIONS+=("$option_num) Install with uv (recommended)")
        MENU_MAP+=("uv")
        ((option_num++))
    fi
    
    # Add pipx option if available
    if [[ "$USE_PIPX" == "true" ]]; then
        MENU_OPTIONS+=("$option_num) Install with pipx")
        MENU_MAP+=("pipx")
        ((option_num++))
    fi
    
    # Always add venv option
    MENU_OPTIONS+=("$option_num) Install with virtual environment")
    MENU_MAP+=("venv")
    ((option_num++))
    
    # Add development option if in repo
    if [[ "$IN_REPO" == "true" ]]; then
        MENU_OPTIONS+=("$option_num) Install from current directory (development)")
        MENU_MAP+=("dev")
        ((option_num++))
    fi
    
    # Add option to install missing tools
    if [[ "$USE_UV" == "false" ]]; then
        MENU_OPTIONS+=("$option_num) Install uv first (fast Python package manager)")
        MENU_MAP+=("install_uv")
        ((option_num++))
    fi
    
    if [[ "$USE_PIPX" == "false" ]] && command_exists brew; then
        MENU_OPTIONS+=("$option_num) Install pipx first (isolated app installer)")
        MENU_MAP+=("install_pipx")
        ((option_num++))
    fi
    
    # Display menu
    for option in "${MENU_OPTIONS[@]}"; do
        echo "$option"
    done
    
    read -p "Choice [1-$((option_num-1))]: " USER_CHOICE
    
    # Validate choice
    if [[ "$USER_CHOICE" -lt 1 ]] || [[ "$USER_CHOICE" -gt $((option_num-1)) ]]; then
        echo -e "${RED}Invalid choice${NC}"
        exit 1
    fi
    
    INSTALL_METHOD="${MENU_MAP[$((USER_CHOICE-1))]}"
    
    # Handle tool installation requests
    if [[ "$INSTALL_METHOD" == "install_uv" ]]; then
        echo -e "${YELLOW}Installing uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        USE_UV=true
        echo -e "${GREEN}✓ uv installed successfully${NC}"
        echo -e "${YELLOW}Please restart the installation script${NC}"
        exit 0
    elif [[ "$INSTALL_METHOD" == "install_pipx" ]]; then
        echo -e "${YELLOW}Installing pipx...${NC}"
        if command_exists brew; then
            brew install pipx
            pipx ensurepath
            export PATH="$HOME/.local/bin:$PATH"
            USE_PIPX=true
            echo -e "${GREEN}✓ pipx installed successfully${NC}"
            echo -e "${YELLOW}Please restart the installation script${NC}"
            exit 0
        else
            echo -e "${RED}Homebrew not found. Please install pipx manually.${NC}"
            exit 1
        fi
    fi
else
    # Linux installation options
    MENU_OPTIONS=()
    MENU_MAP=()
    
    option_num=1
    
    # Add uv option if available
    if [[ "$USE_UV" == "true" ]]; then
        MENU_OPTIONS+=("$option_num) Install with uv (recommended)")
        MENU_MAP+=("uv")
        ((option_num++))
    fi
    
    # Add pipx option if available
    if [[ "$USE_PIPX" == "true" ]]; then
        MENU_OPTIONS+=("$option_num) Install with pipx")
        MENU_MAP+=("pipx")
        ((option_num++))
    fi
    
    # Default options
    MENU_OPTIONS+=("$option_num) Install from GitHub")
    MENU_MAP+=("github")
    ((option_num++))
    
    if [[ "$IN_REPO" == "true" ]]; then
        MENU_OPTIONS+=("$option_num) Install from current directory (development)")
        MENU_MAP+=("dev")
        ((option_num++))
    fi
    
    MENU_OPTIONS+=("$option_num) Install with pip (when published to PyPI)")
    MENU_MAP+=("pip")
    ((option_num++))
    
    # Add option to install missing tools
    if [[ "$USE_UV" == "false" ]]; then
        MENU_OPTIONS+=("$option_num) Install uv first (fast Python package manager)")
        MENU_MAP+=("install_uv")
        ((option_num++))
    fi
    
    # Display menu
    for option in "${MENU_OPTIONS[@]}"; do
        echo "$option"
    done
    
    read -p "Choice [1-$((option_num-1))]: " USER_CHOICE
    
    # Validate choice
    if [[ "$USER_CHOICE" -lt 1 ]] || [[ "$USER_CHOICE" -gt $((option_num-1)) ]]; then
        echo -e "${RED}Invalid choice${NC}"
        exit 1
    fi
    
    INSTALL_METHOD="${MENU_MAP[$((USER_CHOICE-1))]}"
    
    # Handle tool installation requests
    if [[ "$INSTALL_METHOD" == "install_uv" ]]; then
        echo -e "${YELLOW}Installing uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        USE_UV=true
        echo -e "${GREEN}✓ uv installed successfully${NC}"
        echo -e "${YELLOW}Please restart the installation script${NC}"
        exit 0
    fi
fi

# Handle installation based on method
case $INSTALL_METHOD in
    uv)
        echo -e "${BLUE}Installing with uv...${NC}"
        
        INSTALL_PATH=$(get_install_source)
        
        # Check if already installed with uv
        if uv tool list 2>/dev/null | grep -q "grafana-publisher"; then
            echo -e "${YELLOW}Grafana Publisher is already installed with uv${NC}"
            echo -e "${YELLOW}Reinstalling with latest version...${NC}"
            uv tool install "$INSTALL_PATH" --force
        else
            echo -e "${YELLOW}Installing package with uv...${NC}"
            # Try normal install first, if it fails due to existing executables, use --force
            if ! uv tool install "$INSTALL_PATH" 2>/dev/null; then
                echo -e "${YELLOW}Executables exist, forcing installation...${NC}"
                uv tool install "$INSTALL_PATH" --force
            fi
        fi
        
        # Copy config files  
        mkdir -p "$CONFIG_DIR"
        if [ -f "$INSTALL_PATH/config/config.example.yaml" ]; then
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.yaml"
            cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.example.yaml"
        fi
        
        # Create symlink for gp command
        ln -sf "$HOME/.local/bin/grafana-publisher" "$HOME/.local/bin/gp" 2>/dev/null || true
        
        # Cleanup if we cloned
        if [[ "$INSTALL_PATH" != "." ]]; then
            cd /
            rm -rf "$(dirname "$INSTALL_PATH")"
        fi
        ;;
        
    pipx)
        echo -e "${BLUE}Installing with pipx...${NC}"
        
        INSTALL_PATH=$(get_install_source)
        
        # Check if already installed with pipx
        if pipx list 2>/dev/null | grep -q "grafana-publisher"; then
            echo -e "${YELLOW}Grafana Publisher is already installed with pipx${NC}"
            echo -e "${YELLOW}Reinstalling to latest version...${NC}"
            pipx uninstall grafana-publisher >/dev/null 2>&1
            pipx install "$INSTALL_PATH"
        else
            echo -e "${YELLOW}Installing package with pipx...${NC}"
            pipx install "$INSTALL_PATH"
        fi
        
        # Copy config files  
        mkdir -p "$CONFIG_DIR"
        if [ -f "$INSTALL_PATH/config/config.example.yaml" ]; then
            [ ! -f "$CONFIG_DIR/config.yaml" ] && cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.yaml"
            cp "$INSTALL_PATH/config/config.example.yaml" "$CONFIG_DIR/config.example.yaml"
        fi
        
        # Create symlink for gp command
        ln -sf "$HOME/.local/bin/grafana-publisher" "$HOME/.local/bin/gp" 2>/dev/null || true
        
        # Cleanup if we cloned
        if [[ "$INSTALL_PATH" != "." ]]; then
            cd /
            rm -rf "$(dirname "$INSTALL_PATH")"
        fi
        ;;
        
    venv)
        echo -e "${BLUE}Installing with virtual environment...${NC}"
        
        # Create venv directory
        mkdir -p "$(dirname "$VENV_DIR")"
        
        # Create virtual environment
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
        
        # Activate and install
        source "$VENV_DIR/bin/activate"
        
        INSTALL_PATH=$(get_install_source)
        
        echo -e "${YELLOW}Installing package...${NC}"
        pip install "$INSTALL_PATH"
        
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
        if [[ "$INSTALL_PATH" != "." ]]; then
            cd /
            rm -rf "$(dirname "$INSTALL_PATH")"
        fi
        
        deactivate
        ;;
        
    dev)
        echo -e "${BLUE}Installing from current directory (development)...${NC}"
        
        if [ ! -f "pyproject.toml" ]; then
            echo -e "${RED}✗ pyproject.toml not found. Please run from grafana-publisher directory${NC}"
            exit 1
        fi
        
        # Check if uv is available for development install
        if [[ "$USE_UV" == "true" ]]; then
            echo -e "${YELLOW}Creating development environment with uv...${NC}"
            uv venv
            source .venv/bin/activate
            uv pip install -e ".[dev]"
            
            # Create wrapper script for uv venv
            mkdir -p "$INSTALL_DIR"
            CURRENT_DIR=$(pwd)
            cat > "$INSTALL_DIR/grafana-publisher" << EOF
#!/bin/bash
source "$CURRENT_DIR/.venv/bin/activate"
exec python "$CURRENT_DIR/main.py" "\$@"
EOF
        else
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
        fi
        
        chmod +x "$INSTALL_DIR/grafana-publisher"
        ln -sf "$INSTALL_DIR/grafana-publisher" "$INSTALL_DIR/gp"
        
        # Copy config files
        mkdir -p "$CONFIG_DIR"
        [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
        cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
        
        if [[ "$USE_UV" == "true" ]]; then
            deactivate
        else
            deactivate
        fi
        ;;
        
    github)
        echo -e "${BLUE}Installing from GitHub...${NC}"
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        git clone "$REPO_URL" grafana-publisher
        cd grafana-publisher
        
        # Try to checkout latest stable tag
        LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        if [[ -n "$LATEST_TAG" ]] && [[ ! "$LATEST_TAG" =~ -develop\. ]]; then
            echo -e "${GREEN}Using latest stable release: $LATEST_TAG${NC}"
            git checkout "$LATEST_TAG" >/dev/null 2>&1
        else
            echo -e "${YELLOW}Using main branch${NC}"
            git checkout main >/dev/null 2>&1 || true
        fi
        
        pip3 install --user .
        mkdir -p "$CONFIG_DIR"
        [ ! -f "$CONFIG_DIR/config.yaml" ] && cp config/config.example.yaml "$CONFIG_DIR/config.yaml"
        cp config/config.example.yaml "$CONFIG_DIR/config.example.yaml"
        cd /
        rm -rf "$TEMP_DIR"
        ;;
        
    pip)
        echo -e "${BLUE}Installing from PyPI...${NC}"
        pip3 install --user grafana-publisher
        mkdir -p "$CONFIG_DIR"
        ;;
        
    *)
        echo -e "${RED}Invalid installation method${NC}"
        exit 1
        ;;
esac

# Verify installation
echo ""
echo -e "${YELLOW}Verifying installation...${NC}"

if command_exists grafana-publisher; then
    echo -e "${GREEN}✓ grafana-publisher command is available${NC}"
elif [ -f "$INSTALL_DIR/grafana-publisher" ]; then
    echo -e "${GREEN}✓ grafana-publisher installed at $INSTALL_DIR${NC}"
elif command_exists uv && uv tool list 2>/dev/null | grep -q grafana-publisher; then
    echo -e "${GREEN}✓ grafana-publisher installed with uv${NC}"
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