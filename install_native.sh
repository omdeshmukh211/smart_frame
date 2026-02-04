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

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-pyqt5 \
    python3-yaml \
    mpv \
    ffmpeg \
    x11-xserver-utils

# Install Python packages
echo "Installing Python packages..."
pip3 install --user -r requirements_native.txt

# Create photos directory if it doesn't exist
PHOTOS_DIR="$HOME/Pictures/smart_frame"
if [ ! -d "$PHOTOS_DIR" ]; then
    echo "Creating photos directory: $PHOTOS_DIR"
    mkdir -p "$PHOTOS_DIR"
fi

# Update settings with photos directory
echo "Updating configuration..."
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
