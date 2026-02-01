# PyQt5 Kiosk Mode Setup Guide

This guide explains how to run Smart Frame using PyQt5/QtWebEngine instead of Chromium kiosk mode.

## Overview

The new setup replaces the heavy Chromium browser with a lightweight PyQt5 application that:
- Embeds QtWebEngine (based on Chromium, but more efficient for embedded use)
- Runs your existing Flask app in a background thread
- Displays the UI in a fullscreen window
- Launches external Chromium only for YouTube Music (when needed)

## Prerequisites

- Raspberry Pi 4 with Debian Trixie (Raspberry Pi OS)
- X11 display server running
- Python 3.9+
- Elecrow 7" display (1024x600)

## Quick Install

```bash
# Make install script executable and run it
chmod +x install.sh
sudo ./install.sh
```

## Manual Installation

### 1. Install System Dependencies

```bash
# Update system
sudo apt-get update

# Install PyQt5 with QtWebEngine
sudo apt-get install -y \
    python3-pyqt5 \
    python3-pyqt5.qtwebengine \
    python3-pyqt5.qtwebchannel \
    libqt5webengine5 \
    libqt5webenginewidgets5

# Install Python dependencies
pip3 install -r requirements.txt
```

### 2. Test Before Deployment

Before enabling the systemd service, test the application manually:

```bash
# Test in windowed mode (recommended first)
python3 qt_launcher.py --windowed

# Test in fullscreen mode
python3 qt_launcher.py

# Test with debug logging
python3 qt_launcher.py --debug --windowed
```

**Keyboard shortcuts during testing:**
- `F5` - Reload page
- `F11` - Toggle fullscreen
- `Escape` - Exit (windowed mode only)

### 3. Install Systemd Service

```bash
# Copy service file
sudo cp services/kiosk.service /etc/systemd/system/kiosk.service

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start kiosk.service

# Check status
sudo systemctl status kiosk.service

# Enable autostart on boot
sudo systemctl enable kiosk.service
```

### 4. View Logs

```bash
# Real-time logs
journalctl -u kiosk.service -f

# Application log file
tail -f data/qt_launcher.log
```

## Triggering External Chromium for YouTube Music

The PyQt5 app includes a JavaScript bridge that allows your web UI to launch external Chromium for YouTube Music.

### Method 1: Via JavaScript (Recommended)

Add this to your UI JavaScript:

```javascript
// Check if running in Qt WebEngine
function isQtWebEngine() {
    return typeof qt !== 'undefined' && qt.webChannelTransport;
}

// Launch YouTube Music in external Chromium
function launchYouTubeMusic(artist) {
    if (isQtWebEngine()) {
        // Initialize QWebChannel if not done
        new QWebChannel(qt.webChannelTransport, function(channel) {
            channel.objects.chromiumBridge.launch_youtube_music(artist || "");
        });
    } else {
        // Fallback for regular browser
        window.open('https://music.youtube.com/search?q=' + encodeURIComponent(artist), '_blank');
    }
}

// Stop YouTube Music
function stopYouTubeMusic() {
    if (isQtWebEngine()) {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            channel.objects.chromiumBridge.stop_youtube_music();
        });
    }
}
```

### Method 2: Via Flask API Route

Add a route to your Flask app:

```python
import subprocess
import os

@app.route('/api/launch_music', methods=['POST'])
def launch_music():
    """Launch external Chromium for YouTube Music."""
    data = request.get_json() or {}
    artist = data.get('artist', '')
    
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'start_music.sh')
    
    try:
        if artist:
            subprocess.Popen(['/bin/bash', script_path, artist])
        else:
            subprocess.Popen(['/bin/bash', script_path])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

Then call from JavaScript:
```javascript
fetch('/api/launch_music', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({artist: 'Taylor Swift'})
});
```

## Troubleshooting

### Display Not Showing

1. **Check DISPLAY variable:**
   ```bash
   echo $DISPLAY
   # Should output ":0" or similar
   ```

2. **Verify X11 is running:**
   ```bash
   ps aux | grep Xorg
   ```

3. **Check XAUTHORITY:**
   ```bash
   ls -la ~/.Xauthority
   ```

4. **Try running with explicit display:**
   ```bash
   DISPLAY=:0 python3 qt_launcher.py --windowed
   ```

### Black Screen

1. **Check Flask is running:**
   ```bash
   curl http://127.0.0.1:5000
   ```

2. **Check logs for errors:**
   ```bash
   journalctl -u kiosk.service -n 50
   cat data/qt_launcher.log
   ```

3. **Verify QtWebEngine is installed:**
   ```bash
   python3 -c "from PyQt5.QtWebEngineWidgets import QWebEngineView; print('OK')"
   ```

### Performance Issues

1. **Check memory usage:**
   ```bash
   free -h
   htop
   ```

2. **Reduce memory usage by editing qt_launcher.py:**
   - Disable JavaScript if not needed
   - Reduce JS heap size in QTWEBENGINE_CHROMIUM_FLAGS

3. **Check for swap usage:**
   ```bash
   # Add swap if needed
   sudo fallocate -l 1G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Service Crashes

1. **Check why it stopped:**
   ```bash
   systemctl status kiosk.service
   journalctl -u kiosk.service --no-pager | tail -100
   ```

2. **Increase restart delay in service file if looping:**
   ```ini
   RestartSec=10
   ```

## Performance Comparison

| Metric | Chromium Kiosk | PyQt5/QtWebEngine |
|--------|---------------|-------------------|
| RAM Usage | ~400-600 MB | ~150-250 MB |
| Startup Time | 8-15 seconds | 3-5 seconds |
| CPU Idle | 5-15% | 1-5% |
| GPU Required | Optional | No |

## File Structure

```
smart_frame/
├── qt_launcher.py        # PyQt5 wrapper (NEW)
├── install.sh            # Installation script (NEW)
├── app.py                # Flask application (existing)
├── services/
│   └── kiosk.service     # Systemd service (UPDATED)
├── data/
│   └── qt_launcher.log   # Application logs (NEW)
└── ...
```

## Reverting to Chromium

If you need to revert to the old Chromium-based setup:

```bash
# Stop PyQt5 service
sudo systemctl stop kiosk.service
sudo systemctl disable kiosk.service

# Create old-style service (example)
cat << 'EOF' | sudo tee /etc/systemd/system/kiosk.service
[Unit]
Description=Smart Frame Kiosk (Chromium)
After=graphical.target

[Service]
User=raspberrypi4
Environment=DISPLAY=:0
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/chromium-browser --kiosk --noerrdialogs http://localhost:5000

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kiosk.service
sudo systemctl start kiosk.service
```
