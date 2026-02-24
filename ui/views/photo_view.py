"""
Photo View - Retro Hardware Style
Fullscreen photo slideshow with minimal controls.
Image swaps only, no fade transitions.
"""

import logging
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPen, QBrush

from models.app_state import AppState
from services.photo_service import PhotoService

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class PhotoView(QWidget):
    """
    Photo slideshow view - Retro Hardware Style.
    
    Full-screen photos with discrete image swaps (no fades).
    Minimal control bar at bottom.
    """
    
    def __init__(self, app_state: AppState, photo_service: PhotoService, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.photo_service = photo_service
        self.navigate = navigate_callback
        
        self.current_pixmap = None
        self.is_playing = True
        self.show_controls = True
        self.control_hide_timer = None
        
        self._init_ui()
        self._init_timers()
        
        # Listen for photo updates
        app_state.register_callback('photo_changed', self._on_photo_changed)
    
    def _init_ui(self):
        """Initialize UI - pure black background."""
        self.setStyleSheet("background-color: #000000;")
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _init_timers(self):
        """Initialize timers."""
        # Slideshow timer
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self._next_photo)
        
        # Control bar auto-hide timer
        self.control_timer = QTimer()
        self.control_timer.timeout.connect(self._hide_controls)
        self.control_timer.setSingleShot(True)
    
    def paintEvent(self, event):
        """Paint the photo and controls."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw photo
        if self.current_pixmap and not self.current_pixmap.isNull():
            # Center the photo
            px = (w - self.current_pixmap.width()) // 2
            py = (h - self.current_pixmap.height()) // 2
            painter.drawPixmap(px, py, self.current_pixmap)
        else:
            # No photo placeholder
            painter.setPen(QColor(80, 80, 80))
            font = QFont("Courier New", 24)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignCenter, "[ NO PHOTOS ]")
        
        # Draw controls if visible
        if self.show_controls:
            self._draw_controls(painter)
    
    def _draw_controls(self, painter):
        """Draw the control bar at bottom."""
        w, h = self.width(), self.height()
        
        # Semi-transparent bar at bottom
        bar_h = 60
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.drawRect(0, h - bar_h, w, bar_h)
        
        # Control buttons
        btn_w = 80
        btn_h = 40
        btn_y = h - bar_h + 10
        center_x = w // 2
        spacing = 20
        
        # Previous button
        self._prev_rect = QRectF(center_x - btn_w * 1.5 - spacing, btn_y, btn_w, btn_h)
        self._draw_control_btn(painter, self._prev_rect, "⏮")
        
        # Play/Pause button
        self._play_rect = QRectF(center_x - btn_w // 2, btn_y, btn_w, btn_h)
        play_text = "⏸" if self.is_playing else "▶"
        self._draw_control_btn(painter, self._play_rect, play_text)
        
        # Next button
        self._next_rect = QRectF(center_x + btn_w // 2 + spacing, btn_y, btn_w, btn_h)
        self._draw_control_btn(painter, self._next_rect, "⏭")
        
        # Back button (left side)
        self._back_rect = QRectF(20, btn_y, 100, btn_h)
        self._draw_control_btn(painter, self._back_rect, "← BACK")
        
        # Photo counter (right side)
        count = self.photo_service.get_photo_count() if hasattr(self.photo_service, 'get_photo_count') else 0
        index = self.photo_service.get_current_index() if hasattr(self.photo_service, 'get_current_index') else 0
        
        if count > 0:
            counter_text = f"{index + 1}/{count}"
            painter.setPen(QColor(160, 160, 160))
            font = QFont("Courier New", 14)
            painter.setFont(font)
            painter.drawText(w - 100, btn_y, 80, btn_h, Qt.AlignRight | Qt.AlignVCenter, counter_text)
    
    def _draw_control_btn(self, painter, rect, text):
        """Draw a control button."""
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(rect)
        
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Courier New", 16 if len(text) <= 2 else 12)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text)
    
    def _load_photo(self):
        """Load and display current photo (instant swap, no fade)."""
        photo_path = self.photo_service.get_current_photo_path()
        
        if not photo_path or not Path(photo_path).exists():
            logger.debug(f"No photo available: {photo_path}")
            self.current_pixmap = None
            self.update()
            return
        
        # Check widget has valid size
        if self.width() <= 0 or self.height() <= 60:
            logger.debug(f"Widget has invalid size: {self.width()}x{self.height()}, deferring load")
            QTimer.singleShot(100, self._load_photo)
            return
        
        try:
            pixmap = QPixmap(str(photo_path))
            if pixmap.isNull():
                logger.warning(f"Failed to load image: {photo_path}")
                self.current_pixmap = None
                self.update()
                return
            
            # Scale to fit screen while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.width(),
                self.height() - 60,  # Leave room for controls
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.current_pixmap = scaled_pixmap
            logger.debug(f"Loaded photo: {photo_path.name} scaled to {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            self.update()
            
        except Exception as e:
            logger.error(f"Error loading photo: {e}")
            self.current_pixmap = None
            self.update()
    
    def _next_photo(self):
        """Go to next photo."""
        self.photo_service.next_photo()
        self._load_photo()  # Explicitly load to ensure update
    
    def _previous_photo(self):
        """Go to previous photo."""
        self.photo_service.previous_photo()
        self._load_photo()  # Explicitly load to ensure update
    
    def _toggle_slideshow(self):
        """Toggle slideshow play/pause."""
        if self.is_playing:
            self.slideshow_timer.stop()
            self.is_playing = False
        else:
            interval = self.app_state.get_setting('slideshow_interval', 5) * 1000
            self.slideshow_timer.start(interval)
            self.is_playing = True
        self.update()
    
    def _show_controls_temp(self):
        """Show controls temporarily."""
        self.show_controls = True
        self.update()
        # Auto-hide after 3 seconds
        self.control_timer.start(3000)
    
    def _hide_controls(self):
        """Hide controls."""
        self.show_controls = False
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse clicks."""
        pos = event.pos()
        
        # Always show controls on tap
        self._show_controls_temp()
        
        # Check control buttons if visible
        if self.show_controls:
            if hasattr(self, '_prev_rect') and self._prev_rect.contains(pos.x(), pos.y()):
                self._previous_photo()
                return
            if hasattr(self, '_play_rect') and self._play_rect.contains(pos.x(), pos.y()):
                self._toggle_slideshow()
                return
            if hasattr(self, '_next_rect') and self._next_rect.contains(pos.x(), pos.y()):
                self._next_photo()
                return
            if hasattr(self, '_back_rect') and self._back_rect.contains(pos.x(), pos.y()):
                self._go_back()
                return
    
    def keyPressEvent(self, event):
        """Handle keyboard input."""
        key = event.key()
        
        self._show_controls_temp()
        
        if key == Qt.Key_Escape:
            self._go_back()
        elif key == Qt.Key_Space:
            self._toggle_slideshow()
        elif key == Qt.Key_Left:
            self._previous_photo()
        elif key == Qt.Key_Right:
            self._next_photo()
        else:
            super().keyPressEvent(event)
    
    def _go_back(self):
        """Go back to home."""
        if self.navigate:
            self.navigate(AppState.VIEW_HOME)
    
    def _on_photo_changed(self, index):
        """Handle photo change from service."""
        self._load_photo()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Photo view activated")
        
        # Start slideshow
        interval = self.app_state.get_setting('slideshow_interval', 5) * 1000
        self.slideshow_timer.start(interval)
        self.is_playing = True
        
        # Show controls initially
        self._show_controls_temp()
        
        # Defer photo loading until widget has correct size
        # Use QTimer.singleShot to let Qt process layout first
        QTimer.singleShot(100, self._load_photo)
        self.setFocus()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Photo view deactivated")
        self.slideshow_timer.stop()
        self.control_timer.stop()
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        # Reload photo to fit new size
        if self.current_pixmap:
            self._load_photo()
