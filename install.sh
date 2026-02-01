#!/bin/bash
# ============================================================================
# Smart Frame Installation Script
# ============================================================================
# This script installs all dependencies and configures the system for running
# Smart Frame with PyQt5/QtWebEngine on Raspberry Pi.
#
# Usage:
#   chmod +x install.sh
#   sudo ./install.sh
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/raspberrypi4/projects/smart_frame"
SERVICE_NAME="kiosk.service"
USER="raspberrypi4"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Smart Frame Installation Script${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (sudo)${NC}"
    exit 1
fi

# ============================================================================
# Step 1: System Update
# ============================================================================
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
apt-get update
echo -e "${GREEN}✓ System updated${NC}"
echo ""

# ============================================================================
# Step 2: Install PyQt5 and QtWebEngine
# ============================================================================
echo -e "${YELLOW}Step 2: Installing PyQt5 and QtWebEngine...${NC}"

apt-get install -y \
    python3-pyqt5 \
    python3-pyqt5.qtwebengine \
    python3-pyqt5.qtwebchannel \
    libqt5webengine5 \
    libqt5webenginewidgets5

echo -e "${GREEN}✓ PyQt5 packages installed${NC}"
echo ""

# ============================================================================
# Step 3: Install Python dependencies
# ============================================================================
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"

# Install pip packages (Flask and others from requirements.txt)
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip3 install -r "$PROJECT_DIR/requirements.txt" --break-system-packages 2>/dev/null || \
    pip3 install -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found, skipping pip install${NC}"
fi
echo ""

# ============================================================================
# Step 4: Install optional dependencies for better performance
# ============================================================================
echo -e "${YELLOW}Step 4: Installing optional dependencies...${NC}"

apt-get install -y \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdotool \
    unclutter 2>/dev/null || true

echo -e "${GREEN}✓ Optional dependencies installed${NC}"
echo ""

# ============================================================================
# Step 5: Create data directory and set permissions
# ============================================================================
echo -e "${YELLOW}Step 5: Setting up directories and permissions...${NC}"

# Create data directory if it doesn't exist
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/messages"

# Set ownership
chown -R "$USER:$USER" "$PROJECT_DIR"

# Make scripts executable
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/qt_launcher.py"

echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# ============================================================================
# Step 6: Stop old Chromium-based service (if running)
# ============================================================================
echo -e "${YELLOW}Step 6: Stopping old services...${NC}"

systemctl stop kiosk.service 2>/dev/null || true
systemctl disable kiosk.service 2>/dev/null || true

# Kill any running Chromium instances
pkill -f "chromium" 2>/dev/null || true

echo -e "${GREEN}✓ Old services stopped${NC}"
echo ""

# ============================================================================
# Step 7: Install new systemd service
# ============================================================================
echo -e "${YELLOW}Step 7: Installing systemd service...${NC}"

# Copy service file
cp "$PROJECT_DIR/services/kiosk.service" "/etc/systemd/system/$SERVICE_NAME"

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}✓ Systemd service installed${NC}"
echo ""

# ============================================================================
# Step 8: Create unclutter autostart (hide cursor)
# ============================================================================
echo -e "${YELLOW}Step 8: Configuring cursor hiding...${NC}"

# Create autostart directory
AUTOSTART_DIR="/home/$USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Create unclutter desktop entry
cat > "$AUTOSTART_DIR/unclutter.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Unclutter
Exec=unclutter -idle 0.5 -root
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF

chown -R "$USER:$USER" "/home/$USER/.config"

echo -e "${GREEN}✓ Cursor hiding configured${NC}"
echo ""

# ============================================================================
# Installation Complete
# ============================================================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "To test the application (before enabling autostart):"
echo -e "  ${YELLOW}sudo -u $USER python3 $PROJECT_DIR/qt_launcher.py --windowed${NC}"
echo ""
echo -e "To start the kiosk service:"
echo -e "  ${YELLOW}sudo systemctl start kiosk.service${NC}"
echo ""
echo -e "To enable autostart on boot:"
echo -e "  ${YELLOW}sudo systemctl enable kiosk.service${NC}"
echo ""
echo -e "To view logs:"
echo -e "  ${YELLOW}journalctl -u kiosk.service -f${NC}"
echo ""
echo -e "To stop the service:"
echo -e "  ${YELLOW}sudo systemctl stop kiosk.service${NC}"
echo ""
