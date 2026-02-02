#!/bin/bash
#
# Photo Slideshow Feature - Quick Setup Script
# Run this on your Raspberry Pi to set up the photo slideshow feature
#

set -e  # Exit on error

echo "=========================================="
echo "Smart Frame - Photo Slideshow Setup"
echo "=========================================="
echo ""

# Define paths
PROJECT_DIR="/home/raspberrypi4/projects/smart_frame"
PHOTOS_DIR="$PROJECT_DIR/photos"

echo "Project directory: $PROJECT_DIR"
echo "Photos directory: $PHOTOS_DIR"
echo ""

# Step 1: Install Python dependencies
echo "Step 1: Installing Python dependencies..."
cd "$PROJECT_DIR"
pip3 install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Step 2: Create photos directory
echo "Step 2: Creating photos directory..."
if [ ! -d "$PHOTOS_DIR" ]; then
    mkdir -p "$PHOTOS_DIR"
    echo "✓ Created directory: $PHOTOS_DIR"
else
    echo "✓ Directory already exists: $PHOTOS_DIR"
fi
echo ""

# Step 3: Set permissions
echo "Step 3: Setting permissions..."
chmod 755 "$PHOTOS_DIR"
echo "✓ Permissions set"
echo ""

# Step 4: Check for photos
echo "Step 4: Checking photo collection..."
PHOTO_COUNT=$(find "$PHOTOS_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l)
echo "Found $PHOTO_COUNT photos in $PHOTOS_DIR"
echo ""

if [ "$PHOTO_COUNT" -eq 0 ]; then
    echo "⚠️  WARNING: No photos found!"
    echo ""
    echo "To add photos, use one of these methods:"
    echo ""
    echo "1. Copy from USB drive:"
    echo "   cp /media/usb/my_photos/*.jpg $PHOTOS_DIR/"
    echo ""
    echo "2. Download from network:"
    echo "   scp user@computer:/path/to/photos/* $PHOTOS_DIR/"
    echo ""
    echo "3. Use rsync for large collections:"
    echo "   rsync -av --progress /source/photos/ $PHOTOS_DIR/"
    echo ""
else
    echo "✓ Photo collection ready"
    echo ""
fi

# Step 5: Optimize photos (optional)
if [ "$PHOTO_COUNT" -gt 0 ]; then
    echo "Step 5: Photo optimization (optional)..."
    echo ""
    echo "Would you like to optimize photos for better performance? [y/N]"
    read -r OPTIMIZE
    
    if [ "$OPTIMIZE" = "y" ] || [ "$OPTIMIZE" = "Y" ]; then
        # Check if ImageMagick is installed
        if ! command -v convert &> /dev/null; then
            echo "Installing ImageMagick..."
            sudo apt-get update
            sudo apt-get install -y imagemagick
        fi
        
        echo "Optimizing photos (this may take a while)..."
        cd "$PHOTOS_DIR"
        
        # Create backup directory
        BACKUP_DIR="$PHOTOS_DIR/originals_backup"
        mkdir -p "$BACKUP_DIR"
        
        # Optimize each photo
        OPTIMIZED=0
        for img in $(find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \)); do
            # Skip if already optimized
            if [ ! -f "$BACKUP_DIR/$img" ]; then
                # Get file size
                SIZE=$(stat -f%z "$img" 2>/dev/null || stat -c%s "$img" 2>/dev/null)
                
                # Only optimize if larger than 2MB
                if [ "$SIZE" -gt 2097152 ]; then
                    echo "  Optimizing: $img"
                    cp "$img" "$BACKUP_DIR/$img"
                    convert "$img" -resize 1024x600\> -quality 85 "$img"
                    OPTIMIZED=$((OPTIMIZED + 1))
                fi
            fi
        done
        
        echo "✓ Optimized $OPTIMIZED photos"
        echo "✓ Original photos backed up to: $BACKUP_DIR"
    else
        echo "Skipping optimization"
    fi
    echo ""
fi

# Step 6: Restart Flask app
echo "Setup complete!"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. If running as a service, restart it:"
echo "   sudo systemctl restart smart_frame"
echo ""
echo "2. If running manually:"
echo "   cd $PROJECT_DIR"
echo "   python3 app.py"
echo ""
echo "3. Open the Smart Frame UI in your browser"
echo "   The photo slideshow will start automatically on the clock screen"
echo ""
echo "=========================================="
echo "Configuration:"
echo "=========================================="
echo ""
echo "• Auto-advance interval: 10 minutes"
echo "• Tap photo to advance manually"
echo "• Photos loop continuously"
echo ""
echo "For more information, see:"
echo "  $PROJECT_DIR/docs/PHOTO_SLIDESHOW_SETUP.md"
echo ""
echo "=========================================="
