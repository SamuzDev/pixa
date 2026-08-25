#!/usr/bin/env bash

# pixa installer
# Usage: curl -fsSL https://raw.githubusercontent.com/SamuzDev/pixa/main/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'

REPO="SamuzDev/pixa"
INSTALL_DIR="$HOME/.local/share/pixa"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"
BINARY_NAME="pixa"

info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

check_python() {
    command -v python3 &> /dev/null || error "python3 not found. Install Python 3.10+."

    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        error "Python 3.10+ required. You have: $(python3 --version 2>&1)"
    fi
    success "Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
}

install() {
    echo ""
    echo -e "${CYAN}     ╔═══════════════════════════════╗${NC}"
    echo -e "${CYAN}     ║        ██╗  ██╗ █████╗ ███████╗██╗  ██╗${NC}"
    echo -e "${CYAN}     ║        ██║  ██║██╔══██╗██╔════╝██║ ██╔╝${NC}"
    echo -e "${CYAN}     ║        ███████║███████║███████╗█████╔╝${NC}"
    echo -e "${CYAN}     ║        ██╔══██║██╔══██║╚════██║██╔═██╗${NC}"
    echo -e "${CYAN}     ║        ██║  ██║██║  ██║███████║██║  ██╗${NC}"
    echo -e "${CYAN}     ║        ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝${NC}"
    echo -e "${CYAN}     ║      Dot-style wallpaper generator${NC}"
    echo -e "${CYAN}     ╚═══════════════════════════════╝${NC}"
    echo ""

    info "Checking requirements..."
    check_python

    info "Setting up installation..."
    rm -rf "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR" "$BIN_DIR"

    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"

    info "Downloading and installing pixa..."
    pip install git+"https://github.com/${REPO}.git" --quiet --disable-pip-version-check || {
        warn "Direct install failed, cloning manually..."
        git clone --depth 1 "https://github.com/${REPO}.git" "$INSTALL_DIR/src"
        pip install "$INSTALL_DIR/src" --quiet --disable-pip-version-check
    }

    info "Creating launcher..."
    cat > "$BIN_DIR/$BINARY_NAME" << 'LAUNCHER'
#!/bin/bash
source "$HOME/.local/share/pixa/venv/bin/activate"
exec python -m pixa "$@"
LAUNCHER
    chmod +x "$BIN_DIR/$BINARY_NAME"
    deactivate

    setup_path

    echo ""
    success "Installation complete!"
    echo ""
    echo -e "  Run:   ${WHITE}pixa${NC} <image>"
    echo -e "  Help:  ${WHITE}pixa -h${NC}"
    echo ""
    echo -e "  ${DIM}Examples:${NC}"
    echo -e "  ${DIM}pixa photo.jpg${NC}"
    echo -e "  ${DIM}pixa photo.jpg --mode color -o wallpaper.png${NC}"
    echo ""
}

setup_path() {
    if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
        return
    fi

    local shell_name
    shell_name=$(basename "${SHELL:-/bin/bash}")

    case "$shell_name" in
        fish)
            local fish_dir="$HOME/.config/fish/conf.d"
            mkdir -p "$fish_dir"
            local fish_file="$fish_dir/pixa.fish"
            if [ ! -f "$fish_file" ] || ! grep -q 'pixa' "$fish_file" 2>/dev/null; then
                cat > "$fish_file" << 'FISH'
set -gx PATH "$HOME/.local/bin" $PATH
FISH
                success "Created fish config: $fish_file"
            fi
            echo -e "  ${DIM}Restart fish or run: source $fish_file${NC}"
            ;;
        zsh)
            add_to_unix_config "$HOME/.zshrc"
            ;;
        bash|*)
            add_to_unix_config "$HOME/.bashrc"
            ;;
    esac
}

add_to_unix_config() {
    local config_file="$1"
    if [ -f "$config_file" ]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$config_file" 2>/dev/null; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$config_file"
            success "Added ~/.local/bin to PATH in $config_file"
            echo -e "  ${DIM}Restart your shell or run: source $config_file${NC}"
        else
            success "PATH already configured in $config_file"
        fi
    else
        warn "Add to your shell config:"
        echo -e "  ${DIM}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
}

uninstall() {
    echo ""
    info "Uninstalling pixa..."
    rm -f "$BIN_DIR/$BINARY_NAME"
    rm -rf "$INSTALL_DIR"
    rm -f "$HOME/.config/fish/conf.d/pixa.fish"
    success "Uninstalled!"
    echo ""
}

case "${1:-install}" in
    install) install ;;
    uninstall) uninstall ;;
    *)
        echo "Usage: $0 [install|uninstall]"
        exit 1
        ;;
esac
