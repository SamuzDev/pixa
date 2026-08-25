#!/usr/bin/env bash

# pixa installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Samuz/pixa/main/install.sh | bash

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

info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Check Python 3.10+
check_python() {
    command -v python3 &> /dev/null || error "python3 not found. Install Python 3.10+."

    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        error "Python 3.10+ required. You have: $(python3 --version 2>&1)"
    fi
    success "Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
}

# Install
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

    info "Installing pixa..."
    if ! python3 -m pip install . --quiet --disable-pip-version-check 2>/dev/null; then
        warn "pip install failed, trying with --user..."
        python3 -m pip install . --user --quiet --disable-pip-version-check || error "Installation failed."
    fi

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

# Uninstall
uninstall() {
    echo ""
    info "Uninstalling pixa..."
    python3 -m pip uninstall pixa -y --quiet 2>/dev/null || warn "pixa was not installed via pip"
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
