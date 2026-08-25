#!/usr/bin/env bash

# Build script for pixa binaries
# Usage: ./scripts/build.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${BLUE}▸${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Check dependencies
if ! command -v python3 &> /dev/null; then
    error "python3 not found"
fi

# Create build directory
BUILD_DIR="dist"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create venv for building
BUILD_VENV=".build-venv"
rm -rf "$BUILD_VENV"
info "Creating build environment..."
python3 -m venv "$BUILD_VENV"
source "$BUILD_VENV/bin/activate"

# Install all dependencies
info "Installing dependencies..."
pip install pyinstaller --quiet --disable-pip-version-check
pip install -e . --quiet --disable-pip-version-check

info "Building binary..."
pyinstaller \
    --onefile \
    --strip \
    --name pixa \
    --paths . \
    --noconfirm \
    --clean \
    pixa.py

# PyInstaller outputs to dist/, just clean up build artifacts
rm -rf build pixa.spec

# Cleanup
deactivate
rm -rf "$BUILD_VENV"

success "Binary built: $BUILD_DIR/pixa"
echo ""
echo "Platform: $(uname -s)-$(uname -m)"
echo "Size: $(du -h "$BUILD_DIR/pixa" | cut -f1)"
