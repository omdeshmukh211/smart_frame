"""
Home View - Retro Hardware Style
Clock, photo slideshow, mic toggle, day/night indicator.
Pure black background, monospace text.
"""

import logging
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QColor, QPixmap

from models.app_state import AppState

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class HomeView(QWidget):
    """
    Home screen - Retro Hardware Style.
    
    Elements:
    - Large digital clock (top-left)
    - Mic icon (top-right) - toggle voice commands
    - Photo slideshow in center
    - Subtle hint: "Tap for Menu"
    - Day/Night indicator (sun/moon)
    """
    
    # Orion constellation star positions (normalized 0-1)
    ORION_STARS = [
        # Belt
        (0.45, 0.45, 2),
        (0.50, 0.46, 2),
        (0.55, 0.47, 2),
        # Shoulders
        (0.38, 0.30, 3),
        (0.62, 0.32, 3),
        # Feet
        (0.35, 0.70, 2),
        (0.60, 0.68, 3),
        # Sword
        (0.48, 0.52, 1),
        (0.50, 0.56, 1),
        (0.52, 0.60, 1),
    ]
    
    def __init__(self, app_state: AppState, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        
        self.is_day_mode = True
        self.mic_enabled = False
        self.current_photo = None
        self.photo_index = 0
        
        self._init_ui()
        self._init_timers()
    
    def _init_ui(self):
        """Initialize UI - pure black background."""
        self.setStyleSheet("background-color: #000000;")
        
        # We'll paint most things in paintEvent for full control
        # But use some labels for text
        
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _init_timers(self):
        """Initialize timers."""
        # Clock update
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        
        # Day/night check
        self.daynight_timer = QTimer()
        self.daynight_timer.timeout.connect(self._check_day_night)
        self.daynight_timer.start(60000)  # Every minute
        
        # Slideshow timer
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self._next_photo)
        interval = self.app_state.get_setting('slideshow_interval', 5) * 1000
        self.slideshow_timer.start(interval)
        
        # Repaint timer
        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(1000)
        
        self._check_day_night()
        self._update_clock()
    
    def _update_clock(self):
        """Update clock time."""
        self.update()
    
    def _check_day_night(self):
        """Check if day or night mode."""
        hour = datetime.now().hour
        self.is_day_mode = 6 <= hour < 18
        self.update()
    
    def _next_photo(self):
        """Advance to next photo (image swap, no animation)."""
        # Photo service will handle this
        self.update()
    
    def paintEvent(self, event):
        """Paint the home screen."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw background elements based on day/night
        if self.is_day_mode:
            self._draw_sun(painter)
        else:
            self._draw_night_sky(painter)
            self._draw_moon(painter)
        
        # Draw clock (top-left)
        self._draw_clock(painter)
        
        # Draw mic icon (top-right)
        self._draw_mic_icon(painter)
        
        # Draw photo area (center)
        self._draw_photo_area(painter)
        
        # Draw hint (bottom)
        self._draw_hint(painter)
    
    def _draw_sun(self, painter):
        """Draw small yellow sun at top-left edge."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 220, 80)))  # Yellow
        
        # Sun position - top-left, partially off-screen
        sun_x = 30
        sun_y = 30
        sun_r = 20
        
        painter.drawEllipse(sun_x - sun_r, sun_y - sun_r, sun_r * 2, sun_r * 2)
        
        # Simple rays
        painter.setPen(QPen(QColor(255, 220, 80), 2))
        for i in range(8):
            import math
            angle = i * 45 * math.pi / 180
            x1 = sun_x + sun_r * 1.3 * math.cos(angle)
            y1 = sun_y + sun_r * 1.3 * math.sin(angle)
            x2 = sun_x + sun_r * 1.8 * math.cos(angle)
            y2 = sun_y + sun_r * 1.8 * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_night_sky(self, painter):
        """Draw Orion constellation faintly in background."""
        painter.setPen(Qt.NoPen)
        
        w, h = self.width(), self.height()
        
        for star_x, star_y, size in self.ORION_STARS:
            x = int(star_x * w)
            y = int(star_y * h)
            
            # Subtle star color
            opacity = 40 + size * 15  # 55-85 opacity
            painter.setBrush(QBrush(QColor(200, 200, 220, opacity)))
            painter.drawEllipse(x - size, y - size, size * 2, size * 2)
    
    def _draw_moon(self, painter):
        """Draw crescent moon at top-left."""
        moon_x = 35
        moon_y = 35
        moon_r = 18
        
        # Main moon circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(230, 230, 210)))  # Pale yellow
        painter.drawEllipse(moon_x - moon_r, moon_y - moon_r, moon_r * 2, moon_r * 2)
        
        # Dark overlay for crescent effect
        painter.setBrush(QBrush(QColor(0, 0, 0)))  # Black
        painter.drawEllipse(moon_x - moon_r + 10, moon_y - moon_r - 2, 
                          moon_r * 2 - 4, moon_r * 2)
    
    def _draw_clock(self, painter):
        """Draw large digital clock."""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%a %d %b")
        
        # Time - large monospace
        painter.setPen(QColor(240, 240, 230))  # Off-white
        font = QFont("Courier New", 72, QFont.Bold)
        painter.setFont(font)
        painter.drawText(80, 120, time_str)
        
        # Date - smaller
        font = QFont("Courier New", 20)
        painter.setFont(font)
        painter.setPen(QColor(160, 160, 150))  # Dimmer
        painter.drawText(80, 160, date_str)
    
    def _draw_mic_icon(self, painter):
        """Draw mic icon at top-right."""
        w = self.width()
        mic_x = w - 60
        mic_y = 40
        
        # Mic color based on state
        if self.mic_enabled:
            color = QColor(100, 255, 100)  # Green when active
        else:
            color = QColor(120, 120, 120)  # Gray when off
        
        painter.setPen(QPen(color, 3))
        painter.setBrush(Qt.NoBrush)
        
        # Simple mic shape - rectangle with rounded top
        painter.drawRoundedRect(mic_x - 8, mic_y - 15, 16, 25, 8, 8)
        # Stand
        painter.drawLine(mic_x, mic_y + 12, mic_x, mic_y + 20)
        painter.drawLine(mic_x - 10, mic_y + 20, mic_x + 10, mic_y + 20)
        
        # Store mic rect for click detection
        self._mic_rect = QRectF(mic_x - 20, mic_y - 25, 40, 55)
    
    def _draw_photo_area(self, painter):
        """Draw photo slideshow area in center."""
        w, h = self.width(), self.height()
        
        # Photo area dimensions
        photo_w = 500
        photo_h = 350
        photo_x = (w - photo_w) // 2
        photo_y = (h - photo_h) // 2 + 20
        
        # Border
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRect(photo_x, photo_y, photo_w, photo_h)
        
        # Try to draw current photo
        photo_path = self.app_state.get_current_photo_path() if hasattr(self.app_state, 'get_current_photo_path') else None
        
        if photo_path:
            try:
                pixmap = QPixmap(photo_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(photo_w - 4, photo_h - 4, 
                                          Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    px = photo_x + (photo_w - scaled.width()) // 2
                    py = photo_y + (photo_h - scaled.height()) // 2
                    painter.drawPixmap(px, py, scaled)
                    return
            except:
                pass
        
        # Placeholder if no photo
        painter.setPen(QColor(60, 60, 60))
        font = QFont("Courier New", 24)
        painter.setFont(font)
        painter.drawText(photo_x, photo_y, photo_w, photo_h, 
                        Qt.AlignCenter, "[ PHOTOS ]")
        
        # Store photo rect for click detection
        self._photo_rect = QRectF(photo_x, photo_y, photo_w, photo_h)
    
    def _draw_hint(self, painter):
        """Draw subtle hint at bottom."""
        w, h = self.width(), self.height()
        
        painter.setPen(QColor(80, 80, 80))  # Very subtle
        font = QFont("Courier New", 14)
        painter.setFont(font)
        painter.drawText(0, h - 40, w, 30, Qt.AlignCenter, "Tap for Menu")
    
    def mousePressEvent(self, event):
        """Handle tap - go to menu."""
        pos = event.pos()
        
        # Check if mic icon tapped
        if hasattr(self, '_mic_rect') and self._mic_rect.contains(pos.x(), pos.y()):
            self.mic_enabled = not self.mic_enabled
            logger.info(f"Mic toggled: {self.mic_enabled}")
            self.update()
            return
        
        # Check if photo area tapped
        if hasattr(self, '_photo_rect') and self._photo_rect.contains(pos.x(), pos.y()):
            self.navigate(AppState.VIEW_PHOTOS)
            return
        
        # Any other tap goes to menu
        self.navigate(AppState.VIEW_MENU)
    
    def keyPressEvent(self, event):
        """Handle key press."""
        if event.key() == Qt.Key_Escape:
            self.navigate(AppState.VIEW_IDLE)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.navigate(AppState.VIEW_MENU)
        else:
            super().keyPressEvent(event)
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Home view activated")
        self.clock_timer.start(1000)
        self.repaint_timer.start(1000)
        self._check_day_night()
        self.update()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Home view deactivated")
        # Keep clock running for accuracy
