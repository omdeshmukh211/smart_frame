#!/bin/bash
# Smart Frame Launcher - Native PyQt5 Version
# Use this to start Smart Frame in production

# Set working directory to script location
cd "$(dirname "$0")"

# Ensure X11 display is set
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

# Set Qt platform to X11
export QT_QPA_PLATFORM=xcb

# Disable screen blanking (kiosk mode)
if command -v xset &> /dev/null; then
    xset s off
    xset -dpms
    xset s noblank
fi

# Hide mouse cursor after 3 seconds of inactivity
if command -v unclutter &> /dev/null; then
    unclutter -idle 3 -root &
fi

# Start Smart Frame
echo "Starting Smart Frame (Native PyQt5)..."
python3 main.py "$@"
