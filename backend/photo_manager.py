"""
Photo Manager - Backend module for photo slideshow functionality
Manages photo scanning, sequencing, and serving for the smart frame.
"""

import os
import random
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PhotoManager:
    """
    Manages photo slideshow functionality.
    
    Features:
    - Scans photo directory on initialization
    - Maintains current photo index
    - Provides next/previous photo navigation
    - Loops through photos continuously
    - Supports JPG, JPEG, PNG formats
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    
    def __init__(self, photos_dir: str = '/home/raspberrypi4/projects/smart_frame/photos'):
        """
        Initialize the photo manager.
        
        Args:
            photos_dir: Path to directory containing photos
        """
        self.photos_dir = Path(photos_dir)
        self.photos: List[str] = []
        self.current_index: int = 0
        self.scan_photos()
    
    def scan_photos(self) -> int:
        """
        Scan the photos directory and build the photo list.
        
        Returns:
            Number of photos found
        """
        try:
            if not self.photos_dir.exists():
                logger.warning(f"Photos directory does not exist: {self.photos_dir}")
                self.photos = []
                return 0
            
            # Find all supported image files
            self.photos = []
            for ext in self.SUPPORTED_FORMATS:
                # Use glob to find files with this extension
                self.photos.extend(
                    str(p.relative_to(self.photos_dir))
                    for p in self.photos_dir.glob(f'**/*{ext}')
                    if p.is_file()
                )
            
            # Sort for consistent ordering
            self.photos.sort()
            
            # Reset index if no photos or index out of range
            if not self.photos or self.current_index >= len(self.photos):
                self.current_index = 0
            
            logger.info(f"Found {len(self.photos)} photos in {self.photos_dir}")
            return len(self.photos)
            
        except Exception as e:
            logger.error(f"Error scanning photos: {e}")
            self.photos = []
            return 0
    
    def get_photo_count(self) -> int:
        """
        Get the total number of photos available.
        
        Returns:
            Number of photos
        """
        return len(self.photos)
    
    def get_current_photo(self) -> Optional[str]:
        """
        Get the current photo filename.
        
        Returns:
            Current photo filename (relative to photos dir) or None if no photos
        """
        if not self.photos:
            return None
        return self.photos[self.current_index]
    
    def get_next_photo(self) -> Optional[str]:
        """
        Advance to the next photo and return its filename.
        Loops back to the first photo after the last one.
        
        Returns:
            Next photo filename (relative to photos dir) or None if no photos
        """
        if not self.photos:
            return None
        
        # Advance to next photo (with wrapping)
        self.current_index = (self.current_index + 1) % len(self.photos)
        
        logger.debug(f"Advanced to photo {self.current_index + 1}/{len(self.photos)}: {self.photos[self.current_index]}")
        return self.photos[self.current_index]
    
    def get_previous_photo(self) -> Optional[str]:
        """
        Go back to the previous photo and return its filename.
        Loops to the last photo if currently at the first one.
        
        Returns:
            Previous photo filename (relative to photos dir) or None if no photos
        """
        if not self.photos:
            return None
        
        # Go to previous photo (with wrapping)
        self.current_index = (self.current_index - 1) % len(self.photos)
        
        logger.debug(f"Went back to photo {self.current_index + 1}/{len(self.photos)}: {self.photos[self.current_index]}")
        return self.photos[self.current_index]
    
    def shuffle_photos(self):
        """
        Shuffle the photo order randomly.
        Useful for randomized slideshow mode.
        """
        if self.photos:
            random.shuffle(self.photos)
            self.current_index = 0
            logger.info("Photo order shuffled")
    
    def get_photo_path(self, filename: str) -> Path:
        """
        Get the full filesystem path for a photo filename.
        
        Args:
            filename: Photo filename (relative to photos dir)
            
        Returns:
            Full path to the photo file
        """
        return self.photos_dir / filename
    
    def rescan(self) -> int:
        """
        Rescan the photos directory to pick up new/removed photos.
        
        Returns:
            Number of photos found
        """
        logger.info("Rescanning photos directory...")
        return self.scan_photos()


# Singleton instance
_photo_manager_instance: Optional[PhotoManager] = None


def get_photo_manager(photos_dir: str = '/home/raspberrypi4/projects/smart_frame/photos') -> PhotoManager:
    """
    Get the singleton PhotoManager instance.
    
    Args:
        photos_dir: Path to photos directory (only used on first call)
        
    Returns:
        PhotoManager instance
    """
    global _photo_manager_instance
    
    if _photo_manager_instance is None:
        _photo_manager_instance = PhotoManager(photos_dir)
    
    return _photo_manager_instance
