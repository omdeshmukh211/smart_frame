# Photo Slideshow - Quick Reference

## 🚀 Quick Start (Copy to RPi Terminal)

```bash
# 1. Navigate to project
cd /home/raspberrypi4/projects/smart_frame

# 2. Install dependencies
pip3 install Pillow>=9.0.0

# 3. Create photos directory
mkdir -p /home/raspberrypi4/projects/smart_frame/photos

# 4. Add photos (choose one method)
# Method A: From USB
cp /media/usb/my_photos/*.jpg photos/

# Method B: From network
scp user@computer:/path/to/photos/* photos/

# Method C: From rsync
rsync -av --progress /source/photos/ photos/

# 5. Restart Flask app
sudo systemctl restart smart_frame  # If running as service
# OR
python3 app.py  # If running manually
```

---

## 📸 Usage

- **Auto-advance**: Photos change every 10 minutes automatically
- **Manual advance**: Tap/click the photo to skip to next
- **Continuous loop**: Automatically restarts from the beginning

---

## 🔧 API Quick Reference

```bash
# Get current photo
curl http://localhost:5000/api/photos/current

# Advance to next photo
curl -X POST http://localhost:5000/api/photos/next

# Go to previous photo
curl -X POST http://localhost:5000/api/photos/previous

# Rescan photos directory (after adding new photos)
curl -X POST http://localhost:5000/api/photos/rescan
```

---

## ⚙️ Customize Settings

### Change auto-advance time
Edit `ui/photo_slideshow.js` line 11:
```javascript
this.AUTO_ADVANCE_INTERVAL = 10 * 60 * 1000; // Change 10 to desired minutes
```

### Change fade duration
Edit `ui/photo_slideshow.js` line 12:
```javascript
this.FADE_DURATION = 1000; // Change 1000 to desired milliseconds
```

### Change photos directory
Edit `config/settings.yaml`:
```yaml
photos_dir: '/custom/path/to/photos'
```

---

## 🎨 Optimize Photos

```bash
# Install ImageMagick
sudo apt-get install imagemagick

# Resize all photos to fit display
cd /home/raspberrypi4/projects/smart_frame/photos
mogrify -resize 1024x600\> -quality 85 *.jpg
```

---

## 🐛 Troubleshooting

### No photos showing?
```bash
# Check photos exist
ls -lh /home/raspberrypi4/projects/smart_frame/photos/

# Fix permissions
chmod 644 /home/raspberrypi4/projects/smart_frame/photos/*

# Rescan
curl -X POST http://localhost:5000/api/photos/rescan
```

### Photos not advancing?
- Check browser console (F12) for errors
- Try tapping the photo manually
- Check Flask logs: `journalctl -u smart_frame -f`

---

## 📁 File Structure

```
smart_frame/
├── app.py                       # Flask app (MODIFIED)
├── requirements.txt             # Dependencies (MODIFIED)
├── setup_photo_slideshow.sh     # Setup script (NEW)
├── backend/
│   └── photo_manager.py         # Photo logic (NEW)
├── ui/
│   ├── index.html               # HTML (MODIFIED)
│   ├── style.css                # Styles (MODIFIED)
│   └── photo_slideshow.js       # Slideshow controller (NEW)
├── docs/
│   ├── PHOTO_SLIDESHOW_SETUP.md           # Setup guide (NEW)
│   └── PHOTO_SLIDESHOW_IMPLEMENTATION.md  # Implementation (NEW)
└── photos/                      # Your photos go here!
    ├── photo1.jpg
    ├── photo2.png
    └── vacation/
        └── beach.jpg
```

---

## ✅ Features

- ✅ 10-minute auto-advance (configurable)
- ✅ Tap/click to advance manually
- ✅ Smooth 1-second fade transitions
- ✅ Continuous loop through all photos
- ✅ Fits photos properly (maintains aspect ratio)
- ✅ Supports JPG, JPEG, PNG
- ✅ Subdirectory support
- ✅ Memory efficient (only 2 images loaded)
- ✅ Optimized for Raspberry Pi 4

---

## 📚 Full Documentation

See `docs/PHOTO_SLIDESHOW_SETUP.md` for complete guide

---

**Need help?** Check the logs or browser console for errors!
