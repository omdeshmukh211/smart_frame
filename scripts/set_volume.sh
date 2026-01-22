#!/bin/bash
# Set Volume Script
# Sets system volume using amixer or pactl

VOLUME="${1:-70}"

# Validate volume is a number between 0-100
if ! [[ "$VOLUME" =~ ^[0-9]+$ ]] || [ "$VOLUME" -lt 0 ] || [ "$VOLUME" -gt 100 ]; then
    echo "Error: Volume must be a number between 0 and 100"
    exit 1
fi

# Try amixer first (ALSA)
if command -v amixer &> /dev/null; then
    amixer set Master "${VOLUME}%" unmute 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Volume set to ${VOLUME}% using amixer"
        exit 0
    fi
fi

# Fallback to pactl (PulseAudio)
if command -v pactl &> /dev/null; then
    pactl set-sink-volume @DEFAULT_SINK@ "${VOLUME}%" 2>/dev/null
    pactl set-sink-mute @DEFAULT_SINK@ 0 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Volume set to ${VOLUME}% using pactl"
        exit 0
    fi
fi

# Fallback to wpctl (PipeWire)
if command -v wpctl &> /dev/null; then
    # wpctl uses 0.0-1.0 scale
    VOLUME_DECIMAL=$(echo "scale=2; $VOLUME / 100" | bc)
    wpctl set-volume @DEFAULT_AUDIO_SINK@ "$VOLUME_DECIMAL" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Volume set to ${VOLUME}% using wpctl"
        exit 0
    fi
fi

echo "Error: No audio control tool available (amixer, pactl, or wpctl)"
exit 1
