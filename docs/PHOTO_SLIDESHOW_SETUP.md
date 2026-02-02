# Photo Slideshow Feature - Setup Guide

## Overview

This guide explains how to set up and use the photo slideshow feature on your Smart Frame running on Raspberry Pi 4.

The slideshow displays photos from your local photo collection inside the photo frame placeholder on the clock screen, with automatic advancement every 10 minutes and manual tap-to-advance functionality.

---

## Features

✅ **Auto-advance**: Photos change automatically every 10 minutes  
✅ **Manual advance**: Tap/click the photo to immediately skip to the next one  
✅ **Smooth transitions**: 1-second crossfade between photos  
✅ **Continuous loop**: Automatically restarts from the beginning when reaching the last photo  
✅ **Aspect ratio preservation**: Photos are scaled to fit the frame while maintaining proportions  
✅ **Lightweight**: Optimized for Raspberry Pi 4 performance  
✅ **Multiple formats**: Supports JPG, JPEG, and PNG images  

---

## Installation

### 1. Install Required Python Package

```bash
cd /home/raspberrypi4/projects/smart_frame
pip3 install Pillow>=9.0.0
```

Or install all requirements:

```bash
pip3 install -r requirements.txt
```

### 2. Create Photos Directory

```bash
mkdir -p /home/raspberrypi4/projects/smart_frame/photos
```

### 3. Add Your Photos

Copy your photo collection to the photos directory:

```bash
# Example: Copy photos from USB drive
cp /media/usb/my_photos/*.jpg /home/raspberrypi4/projects/smart_frame/photos/

# Example: Download from network
scp user@computer:/path/to/photos/* /home/raspberrypi4/projects/smart_frame/photos/

# Example: Use rsync for large collections
rsync -av --progress /source/photos/ /home/raspberrypi4/projects/smart_frame/photos/
```

**Supported formats**: JPG, JPEG, PNG

### 4. Verify Installation

Check that photos were copied successfully:

```bash
ls -lh /home/raspberrypi4/projects/smart_frame/photos/
```

You should see your image files listed.

---

## Configuration

### Custom Photos Directory (Optional)

If you want to store photos in a different location, edit `config/settings.yaml`:

```yaml
photos_dir: '/path/to/your/photos'
```

### Adjust Auto-Advance Timing (Optional)

To change the 10-minute auto-advance interval, edit `ui/photo_slideshow.js`:

```javascript
// Change this value (in milliseconds)
this.AUTO_ADVANCE_INTERVAL = 10 * 60 * 1000; // 10 minutes

// Examples:
// 5 minutes: 5 * 60 * 1000
// 15 minutes: 15 * 60 * 1000
// 30 minutes: 30 * 60 * 1000
```

### Adjust Fade Duration (Optional)

To change the transition speed, edit `ui/photo_slideshow.js`:

```javascript
this.FADE_DURATION = 1000; // 1 second (1000ms)
```

---

## Usage

### Automatic Operation

Once installed, the slideshow runs automatically:

1. **On startup**: The first photo loads when the clock screen is displayed
2. **Auto-advance**: Every 10 minutes, the next photo is displayed
3. **Continuous loop**: After the last photo, it starts over from the first

### Manual Controls

- **Tap the photo**: Advance to the next photo immediately (also resets the 10-minute timer)

### Adding New Photos

1. Copy new photos to the photos directory
2. Trigger a rescan via API:

```bash
curl -X POST http://localhost:5000/api/photos/rescan
```

Or restart the Flask application to pick up new photos automatically.

---

## API Endpoints

The photo slideshow exposes the following REST API endpoints:

### Get Current Photo

```http
GET /api/photos/current
```

**Response:**
```json
{
  "success": true,
  "photo": "vacation/beach.jpg",
  "index": 5,
  "total": 450
}
```

### Advance to Next Photo

```http
POST /api/photos/next
```

**Response:**
```json
{
  "success": true,
  "photo": "vacation/sunset.jpg",
  "index": 6,
  "total": 450
}
```

### Go to Previous Photo

```http
POST /api/photos/previous
```

**Response:**
```json
{
  "success": true,
  "photo": "vacation/mountain.jpg",
  "index": 4,
  "total": 450
}
```

### Rescan Photos Directory

```http
POST /api/photos/rescan
```

**Response:**
```json
{
  "success": true,
  "count": 450
}
```

### Serve Photo File

```http
GET /photos/<filename>
```

Example: `/photos/vacation/beach.jpg`

---

## Troubleshooting

### No Photos Displayed

**Problem**: Photo frame shows "No photos available"

**Solutions**:
1. Check that photos exist in the directory:
   ```bash
   ls -lh /home/raspberrypi4/projects/smart_frame/photos/
   ```

2. Verify file permissions:
   ```bash
   chmod 644 /home/raspberrypi4/projects/smart_frame/photos/*.jpg
   ```

3. Check Flask logs for errors:
   ```bash
   # If running as service
   journalctl -u smart_frame -f
   
   # If running directly
   # Check terminal output
   ```

4. Trigger a manual rescan:
   ```bash
   curl -X POST http://localhost:5000/api/photos/rescan
   ```

### Photos Not Advancing

**Problem**: Slideshow is stuck on one photo

**Solutions**:
1. Check browser console for JavaScript errors (F12 in most browsers)
2. Verify the auto-advance timer is running:
   - Open browser console
   - Look for log message: "Auto-advance timer triggered"
3. Try manually advancing:
   - Tap the photo
   - Or call API: `curl -X POST http://localhost:5000/api/photos/next`

### Slow Photo Loading

**Problem**: Photos take a long time to load or cause lag

**Solutions**:
1. **Optimize photo sizes**: Large photos (>5MB) can slow down the RPi4. Resize them:
   ```bash
   # Install ImageMagick
   sudo apt-get install imagemagick
   
   # Resize all photos to fit 1024x600 display
   cd /home/raspberrypi4/projects/smart_frame/photos/
   mogrify -resize 1024x600\> -quality 85 *.jpg
   ```

2. **Reduce photo collection size**: Keep only your favorite photos to reduce memory usage

3. **Check available memory**:
   ```bash
   free -h
   ```

### Transitions Not Smooth

**Problem**: Photos appear to "jump" instead of fading

**Solutions**:
1. Ensure CSS transitions are working - check browser console for errors
2. Reduce photo file sizes (see "Slow Photo Loading" above)
3. The transition duration can be adjusted in `photo_slideshow.js`

### Wrong Photo Directory

**Problem**: Flask can't find photos directory

**Solution**: Update the path in `config/settings.yaml`:
```yaml
photos_dir: '/correct/path/to/photos'
```

Then restart the Flask application.

---

## Performance Tips for Raspberry Pi 4

1. **Optimize Photo Sizes**:
   - Keep photos under 2MB each for best performance
   - Resize to display resolution (1024x600) or slightly larger
   - Use JPEG format with 80-85% quality

2. **Limit Photo Collection**:
   - 100-500 photos is a good range for the RPi4
   - Larger collections work but use more memory during scanning

3. **Organize Photos**:
   - Use subdirectories to organize photos (e.g., `/photos/2024/`, `/photos/vacation/`)
   - The slideshow will find all photos in subdirectories automatically

4. **Batch Resize Script**:
   ```bash
   #!/bin/bash
   # resize_photos.sh - Optimize photos for Smart Frame
   
   for img in *.jpg *.JPG *.jpeg *.JPEG *.png *.PNG; do
       if [ -f "$img" ]; then
           convert "$img" -resize 1024x600\> -quality 85 "optimized_$img"
       fi
   done
   ```

---

## File Structure

The photo slideshow feature consists of these files:

```
smart_frame/
├── app.py                          # Flask app (added photo API endpoints)
├── requirements.txt                # Added Pillow dependency
├── backend/
│   └── photo_manager.py            # NEW: Photo management logic
├── ui/
│   ├── index.html                  # Added photo_slideshow.js script tag
│   ├── style.css                   # Added photo slideshow styles
│   └── photo_slideshow.js          # NEW: Frontend slideshow controller
└── photos/                         # Your photo collection
    ├── photo1.jpg
    ├── photo2.png
    └── vacation/
        ├── beach.jpg
        └── sunset.jpg
```

---

## Technical Details

### Backend (Python)

- **Module**: `backend/photo_manager.py`
- **Class**: `PhotoManager`
- **Key Functions**:
  - `scan_photos()`: Scans directory for image files
  - `get_next_photo()`: Returns next photo in sequence
  - `get_current_photo()`: Returns current photo
  - `rescan()`: Refreshes photo list

### Frontend (JavaScript)

- **File**: `ui/photo_slideshow.js`
- **Class**: `PhotoSlideshowController`
- **Key Features**:
  - Crossfade transition using two image elements
  - Auto-advance timer (10 minutes)
  - Click/tap event handling
  - Image preloading for smooth transitions

### API Endpoints (Flask)

- `/api/photos/current` - Get current photo
- `/api/photos/next` - Advance to next photo
- `/api/photos/previous` - Go to previous photo
- `/photos/<filename>` - Serve photo file
- `/api/photos/rescan` - Rescan photos directory

### CSS Styling

- **File**: `ui/style.css`
- **Key Classes**:
  - `.photo-container` - Container for crossfade effect
  - `.photo-image` - Image element with transitions
  - `.photo-image.current` - Currently visible image
  - `.photo-image.next` - Next image (for crossfade)

---

## Advanced Customization

### Random Shuffle Mode

To enable random photo order, modify `backend/photo_manager.py`:

```python
def __init__(self, photos_dir: str = '/home/raspberrypi4/projects/smart_frame/photos'):
    self.photos_dir = Path(photos_dir)
    self.photos: List[str] = []
    self.current_index: int = 0
    self.scan_photos()
    self.shuffle_photos()  # Add this line to shuffle on startup
```

### Different Scaling Modes

To change how photos fit in the frame, edit `ui/style.css`:

```css
.photo-image {
    /* Current: Scale to fit, maintain aspect ratio, centered */
    object-fit: contain;
    
    /* Alternative: Fill entire frame (may crop) */
    /* object-fit: cover; */
    
    /* Alternative: Stretch to fill (distorts aspect ratio) */
    /* object-fit: fill; */
}
```

---

## Support

If you encounter issues:

1. Check the Flask application logs
2. Check browser console (F12) for JavaScript errors
3. Verify photo directory permissions
4. Ensure Pillow is installed correctly
5. Test API endpoints manually with curl

---

## License

This photo slideshow feature is part of the Smart Frame project.

---

**Enjoy your photo memories on your Smart Frame! 📸**
