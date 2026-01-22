#!/bin/bash
# Stop Music Script
# Kills Chromium browser to stop music playback

# Kill Chromium processes
pkill -f "chromium" 2>/dev/null

# Alternative: kill by window class
# wmctrl -c "Chromium" 2>/dev/null

# Wait for processes to terminate
sleep 1

# Force kill if still running
pkill -9 -f "chromium" 2>/dev/null || true

echo "Music stopped"
exit 0
