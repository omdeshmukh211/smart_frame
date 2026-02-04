# Smart Frame - Quick Start Guide

## 🚀 Installation (5 minutes)

### 1. Clone & Install
```bash
cd /home/pi
git clone <your-repo-url> smart_frame
cd smart_frame
chmod +x install_native.sh
./install_native.sh
```

### 2. Add Photos
```bash
# Copy your photos
cp ~/my-photos/*.jpg ~/Pictures/smart_frame/

# Or create symlink
ln -s /media/usb/photos ~/Pictures/smart_frame
```

### 3. Test Run
```bash
# Windowed mode (for testing)
python3 main.py --windowed

# Fullscreen mode
python3 main.py
```

---

## 📱 User Guide

### Navigation
- **Home** → Clock with navigation buttons
- **Photos** → Fullscreen slideshow
- **Music** → YouTube Music player
- **Settings** → Configuration

### Photo Slideshow
1. Click "Photos" from home
2. **Play/Pause** - Toggle auto-advance
3. **Next/Previous** - Manual control
4. **Home** - Return to home screen

### Music Player
1. Click "Music" from home
2. Type song/artist name
3. Click "Search" or press Enter
4. **Play/Pause** - Control playback
5. **Next/Previous** - Navigate queue
6. **Volume** - Adjust with slider

### Settings
- **Slide Interval** - Time between photos (1-60 seconds)
- **Transition** - Fade or instant
- **Autoplay** - Start music on boot
- **Volume** - Default volume level
- **Save** - Persist changes
- **Reboot/Shutdown** - System controls

---

## ⚙️ Configuration

### Edit Settings
```bash
nano config/settings.yaml
```

### Common Settings
```yaml
slideshow_interval: 5      # Photo display time (seconds)
slideshow_transition: fade # Transition style
photos_dir: ~/Pictures     # Photo directory path
volume: 70                 # Default volume (0-100)
music_autoplay: false      # Auto-start music
```

---

## 🔧 Auto-Start on Boot

### Install Service
```bash
# Install
sudo cp services/smart_frame_native.service /etc/systemd/system/
sudo systemctl enable smart_frame_native.service
sudo systemctl start smart_frame_native.service

# Check status
sudo systemctl status smart_frame_native.service

# View logs
journalctl -u smart_frame_native.service -f
```

### Disable Service
```bash
sudo systemctl stop smart_frame_native.service
sudo systemctl disable smart_frame_native.service
```

---

## 🐛 Troubleshooting

### Music not working
```bash
# Check dependencies
which mpv
which yt-dlp

# Install if missing
sudo apt-get install mpv
pip3 install yt-dlp
```

### Photos not showing
```bash
# Check directory
ls -la ~/Pictures/smart_frame/

# Verify path in config
grep photos_dir config/settings.yaml

# Rescan manually
# (automatic every 30 seconds)
```

### Application won't start
```bash
# Check logs
tail -f data/smart_frame.log

# Try windowed mode
python3 main.py --windowed --debug

# Check dependencies
pip3 install -r requirements_native.txt
```

### Black screen
```bash
# Verify X11
echo $DISPLAY  # Should show :0

# Grant X11 access
export DISPLAY=:0
xhost +local:
```

---

## 🎯 Tips & Tricks

### Large Photo Collections
- Service rescans every 30 seconds
- Add photos anytime (no restart needed)
- Subdirectories supported

### Music Queue
- Searches create queue automatically
- Use Next/Previous to navigate
- Queue persists until cleared

### Kiosk Optimization
```bash
# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
sudo apt-get install unclutter
unclutter -idle 3 &

# Auto-start on boot
# Use systemd service (see above)
```

### Performance
- Recommended: 5-10 second slideshow interval
- Fade transitions smooth on Pi 4
- Music uses ~20MB RAM
- Photos scale automatically

---

## 📂 File Locations

| Item | Path |
|------|------|
| Application | `/home/pi/smart_frame/` |
| Main script | `main.py` |
| Settings | `config/settings.yaml` |
| Logs | `data/smart_frame.log` |
| Photos | `~/Pictures/smart_frame/` |
| Service | `/etc/systemd/system/smart_frame_native.service` |

---

## 🔄 Updates

### Update Code
```bash
cd ~/smart_frame
git pull
./install_native.sh  # Reinstall dependencies
```

### Update Dependencies
```bash
pip3 install --upgrade yt-dlp
sudo apt-get update && sudo apt-get upgrade
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Ctrl+Q** | Quit application |
| **F11** | Toggle fullscreen |
| **Escape** | (None - use Home button) |

---

## 🎨 Customization

### Change Button Colors
Edit UI view files:
```python
# ui/views/home_view.py
btn.setStyleSheet("""
    QPushButton {
        background-color: #FF5722;  # Change this
        ...
    }
""")
```

### Change Fonts
Edit view files:
```python
font = QFont("Arial", 20)  # Change family and size
```

### Add Custom View
1. Create `ui/views/my_view.py`
2. Add to `ui/main_window.py` stack
3. Add navigation button

---

## 📊 System Requirements

### Minimum
- Raspberry Pi 3B+
- 512MB RAM available
- Python 3.7+
- X11 display

### Recommended
- Raspberry Pi 4 (2GB+)
- 1GB RAM available
- Python 3.9+
- Touch screen (optional)

---

## 🔐 Security

### Network
- No listening ports
- No incoming connections
- YouTube Music streams only

### File Access
- Read-only photo directory
- Write to config/ and data/ only
- No root required (except reboot/shutdown)

### Updates
- Manual updates only
- No auto-update (yet)
- Review changes before updating

---

## 📞 Getting Help

1. **Check Logs**
   ```bash
   tail -f data/smart_frame.log
   ```

2. **Enable Debug Mode**
   ```bash
   python3 main.py --debug
   ```

3. **Test Components**
   ```bash
   # Test yt-dlp
   yt-dlp --version
   
   # Test mpv
   mpv --version
   
   # Test PyQt5
   python3 -c "from PyQt5 import QtWidgets"
   ```

---

## 🎯 Performance Checklist

- [ ] Photos directory contains images
- [ ] Settings configured (interval, volume)
- [ ] Dependencies installed (mpv, yt-dlp)
- [ ] Service enabled (if auto-start)
- [ ] Screen blanking disabled
- [ ] X11 display accessible
- [ ] Logs show no errors

---

**You're all set! Enjoy your Smart Frame! 🖼️🎵**
