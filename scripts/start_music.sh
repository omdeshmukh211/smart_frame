#!/bin/bash
# Start Music Script
# Launches Chromium with YouTube Music and searches for the specified artist

ARTIST="${1:-}"

# YouTube Music URL
YT_MUSIC_URL="https://music.youtube.com"

# If artist is provided, construct search URL
if [ -n "$ARTIST" ]; then
    # URL encode the artist name
    ENCODED_ARTIST=$(echo "$ARTIST" | sed 's/ /+/g')
    YT_MUSIC_URL="https://music.youtube.com/search?q=${ENCODED_ARTIST}"
fi

# Kill any existing Chromium instances for clean start
pkill -f "chromium.*youtube.music" 2>/dev/null || true

# Wait a moment
sleep 1

# Launch Chromium in kiosk mode
# Adjust the executable path as needed for your system
if command -v chromium-browser &> /dev/null; then
    CHROMIUM_BIN="chromium-browser"
elif command -v chromium &> /dev/null; then
    CHROMIUM_BIN="chromium"
else
    echo "Chromium not found"
    exit 1
fi

# Launch with YouTube Music
$CHROMIUM_BIN \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --autoplay-policy=no-user-gesture-required \
    "$YT_MUSIC_URL" &

echo "Started YouTube Music with artist: $ARTIST"
exit 0
