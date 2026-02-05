#!/bin/bash
# Smart Frame - Native PyQt5 Installation Script
# Raspberry Pi / Debian-based systems

set -e

echo "========================================"
echo "Smart Frame - Native PyQt5 Installation"
echo "========================================"

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install system dependencies (conditionally skip pip/pyqt5 if present)
echo "Checking system packages..."
TO_INSTALL="python3 python3-yaml mpv ffmpeg x11-xserver-utils"

# Add python3-pip if not installed
if ! dpkg -s python3-pip >/dev/null 2>&1; then
    TO_INSTALL="$TO_INSTALL python3-pip"
else
    echo "python3-pip already installed, skipping"
fi

# Add python3-pyqt5 if not installed
if ! dpkg -s python3-pyqt5 >/dev/null 2>&1; then
    TO_INSTALL="$TO_INSTALL python3-pyqt5"
else
    echo "python3-pyqt5 already installed, skipping"
fi

# Add python3-pyqt5.qtmultimedia if not installed
if ! dpkg -s python3-pyqt5.qtmultimedia >/dev/null 2>&1; then
    TO_INSTALL="$TO_INSTALL python3-pyqt5.qtmultimedia"
else
    echo "python3-pyqt5.qtmultimedia already installed, skipping"
fi

echo "Installing system dependencies: $TO_INSTALL"
sudo apt-get install -y $TO_INSTALL

# Install Python packages
echo "Installing Python packages..."
pip3 install --user -r requirements_native.txt

# Create photos directory inside the project if it doesn't exist
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PHOTOS_DIR="$SCRIPT_DIR/photos"
if [ ! -d "$PHOTOS_DIR" ]; then
    echo "Creating photos directory: $PHOTOS_DIR"
    mkdir -p "$PHOTOS_DIR"
fi

# Update settings with photos directory (use absolute path)
echo "Updating configuration..."
escaped_path=$(printf '%s' "$PHOTOS_DIR" | sed 's|/|\\/|g')
sed -i "s|photos_dir:.*|photos_dir: $PHOTOS_DIR|" config/settings.yaml

# Create data directory
mkdir -p data

# Make main.py executable
chmod +x main.py

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "To run Smart Frame:"
echo "  python3 main.py"
echo ""
echo "For fullscreen kiosk mode:"
echo "  python3 main.py"
echo ""
echo "For windowed mode (testing):"
echo "  python3 main.py --windowed"
echo ""
echo "To enable debug logging:"
echo "  python3 main.py --debug"
echo ""
echo "Photos directory: $PHOTOS_DIR"
echo "Add your photos to this directory!"
echo ""
