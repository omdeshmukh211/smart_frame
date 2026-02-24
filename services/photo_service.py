"""
Photo Service
Background photo management with directory watching.
Runs in QThread to avoid blocking UI.
"""

import logging
from pathlib import Path
from typing import List, Optional
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication

from models.app_state import AppState

logger = logging.getLogger(__name__)


class PhotoService(QThread):
    """
    Photo slideshow service.
    
    Features:
    - Scans photo directory
    - Tracks current photo index
    - Provides next/previous navigation
    - Auto-reloads when directory changes
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG', '.gif', '.GIF', '.heic', '.HEIC'}
    
    photos_updated = pyqtSignal(int)  # Emitted when photo list changes
    
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        self.photos: List[Path] = []
        self.current_index = 0
        self._running = False
        
        # Get photos directory from settings
        photos_dir = app_state.get_setting('photos_dir', 'photos')
        photos_path = Path(photos_dir)
        
        # Handle relative paths - resolve relative to app directory
        if not photos_path.is_absolute():
            # Get the directory where the app is running from
            app_dir = Path(__file__).parent.parent
            photos_path = app_dir / photos_dir
        
        # Expand ~ for home directory
        self.photos_dir = photos_path.expanduser().resolve()
        
        # Ensure directory exists
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        
        # Initial scan
        self.scan_photos()
    
    def run(self):
        """Background thread main loop."""
        self._running = True
        logger.info("Photo service started")
        
        # Periodic directory rescan (every 30 seconds)
        while self._running:
            self.msleep(30000)  # 30 seconds
            if self._running:
                old_count = len(self.photos)
                self.scan_photos()
                if len(self.photos) != old_count:
                    logger.info(f"Photo count changed: {old_count} -> {len(self.photos)}")
                    self.photos_updated.emit(len(self.photos))
    
    def stop(self):
        """Stop the service."""
        logger.info("Stopping photo service...")
        self._running = False
        self.wait(2000)  # Wait up to 2 seconds for thread to finish
    
    def scan_photos(self) -> int:
        """
        Scan photos directory and build photo list.
        
        Returns:
            Number of photos found
        """
        try:
            if not self.photos_dir.exists():
                logger.warning(f"Photos directory does not exist: {self.photos_dir}")
                self.photos = []
                self.app_state.set_photo_count(0)
                return 0
            
            # Find all supported image files
            new_photos = []
            for ext in self.SUPPORTED_FORMATS:
                new_photos.extend(self.photos_dir.glob(f'**/*{ext}'))
            
            # Filter to only files (not directories)
            new_photos = [p for p in new_photos if p.is_file()]
            
            # Sort for consistent ordering
            new_photos.sort()
            
            self.photos = new_photos
            
            # Reset index if needed
            if not self.photos:
                self.current_index = 0
            elif self.current_index >= len(self.photos):
                self.current_index = 0
            
            # Update app state
            self.app_state.set_photo_count(len(self.photos))
            
            logger.info(f"Found {len(self.photos)} photos in {self.photos_dir}")
            return len(self.photos)
            
        except Exception as e:
            logger.error(f"Error scanning photos: {e}")
            self.photos = []
            self.app_state.set_photo_count(0)
            return 0
    
    def get_photo_count(self) -> int:
        """Get total number of photos."""
        return len(self.photos)
    
    def get_current_index(self) -> int:
        """Get current photo index."""
        return self.current_index
    
    def get_current_photo_path(self) -> Optional[Path]:
        """
        Get current photo path.
        
        Returns:
            Path to current photo, or None if no photos
        """
        if not self.photos or self.current_index >= len(self.photos):
            return None
        return self.photos[self.current_index]
    
    def next_photo(self):
        """Move to next photo."""
        if not self.photos:
            return
        
        self.current_index = (self.current_index + 1) % len(self.photos)
        self.app_state.set_photo_index(self.current_index)
        logger.debug(f"Next photo: {self.current_index}/{len(self.photos)}")
    
    def previous_photo(self):
        """Move to previous photo."""
        if not self.photos:
            return
        
        self.current_index = (self.current_index - 1) % len(self.photos)
        self.app_state.set_photo_index(self.current_index)
        logger.debug(f"Previous photo: {self.current_index}/{len(self.photos)}")
    
    def set_photo_index(self, index: int):
        """Set photo index directly."""
        if 0 <= index < len(self.photos):
            self.current_index = index
            self.app_state.set_photo_index(self.current_index)
