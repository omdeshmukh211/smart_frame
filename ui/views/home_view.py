"""
Home View - Retro Hardware Style
40%-60% horizontal split: clock on left, photos on right.
Pure black background, monospace text.
"""

import logging
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QColor, QPixmap

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

from models.app_state import AppState

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class HomeView(QWidget):
    """
    Home screen - Retro Hardware Style.
    
    Layout:
    - 40% left: Sun/Moon (top-left), Clock (center)
    - 60% right: Photos (loop every 10 min or on tap), Mic (top-right), Menu button (bottom-right)
    """
    
    def __init__(self, app_state: AppState, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        
        self.is_day_mode = True
        self.mic_enabled = False
        self.current_photo = None
        self.photo_index = 0
        self.transcription_text = ''
        self.show_transcription = False
        self.mic_toggled = None  # Callback for mic toggle
        
        self._init_ui()
        self._init_timers()
    
    def _init_ui(self):
        """Initialize UI - pure black background."""
        self.setStyleSheet("background-color: #000000;")
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
        
        # Slideshow timer - 10 minutes
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self._next_photo)
        self.slideshow_timer.start(10 * 60 * 1000)  # 10 minutes
        
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
        """Advance to next photo (instant swap, no animation)."""
        # Increment photo index
        if hasattr(self.app_state, 'next_photo'):
            self.app_state.next_photo()
        self.update()
    
    def paintEvent(self, event):
        """Paint the home screen with 40%-60% split."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        split_x = int(w * 0.4)  # 40% split line
        
        # LEFT SIDE (40%) - Clock area
        # Draw sun/moon in top-left
        if self.is_day_mode:
            self._draw_sun(painter, 60, 60)
        else:
            self._draw_moon(painter, 60, 60)
        
        # Draw clock in center-left
        self._draw_clock(painter, split_x)
        
        # RIGHT SIDE (60%) - Photo area
        # Draw mic icon (top-right)
        self._draw_mic_icon(painter, w)
        
        # Draw photo area (fills most of right side)
        self._draw_photo_area(painter, split_x, w, h)
        
        # Draw Menu button (bottom-right)
        self._draw_menu_button(painter, w, h)
        
        # Draw transcription if active
        if self.show_transcription and self.transcription_text:
            self._draw_transcription(painter, w, h)
    
    def _draw_sun(self, painter, x, y):
        """Draw larger yellow sun at specified position."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 220, 80)))  # Yellow
        
        sun_r = 40  # Increased size
        
        painter.drawEllipse(x - sun_r, y - sun_r, sun_r * 2, sun_r * 2)
        
        # Simple rays
        painter.setPen(QPen(QColor(255, 220, 80), 3))
        for i in range(8):
            import math
            angle = i * 45 * math.pi / 180
            x1 = x + sun_r * 1.3 * math.cos(angle)
            y1 = y + sun_r * 1.3 * math.sin(angle)
            x2 = x + sun_r * 1.8 * math.cos(angle)
            y2 = y + sun_r * 1.8 * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_moon(self, painter, x, y):
        """Draw larger crescent moon at specified position."""
        moon_r = 38  # Increased size
        
        # Main moon circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(230, 230, 210)))  # Pale yellow
        painter.drawEllipse(x - moon_r, y - moon_r, moon_r * 2, moon_r * 2)
        
        # Dark overlay for crescent effect
        painter.setBrush(QBrush(QColor(0, 0, 0)))  # Black
        painter.drawEllipse(x - moon_r + 20, y - moon_r - 4, 
                          moon_r * 2 - 8, moon_r * 2)
    
    def _draw_clock(self, painter, split_x):
        """Draw large digital clock in left area."""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%a %d %b")
        
        # Center in left area
        clock_x = split_x // 2
        clock_y = self.height() // 2
        
        # Time - large monospace
        painter.setPen(QColor(240, 240, 230))  # Off-white
        font = QFont("Courier New", 64, QFont.Bold)
        painter.setFont(font)
        
        # Get text bounds for centering
        metrics = painter.fontMetrics()
        time_width = metrics.horizontalAdvance(time_str)
        time_height = metrics.height()
        
        painter.drawText(clock_x - time_width // 2, clock_y - 20, time_str)
        
        # Date - smaller, centered below
        font = QFont("Courier New", 18)
        painter.setFont(font)
        painter.setPen(QColor(160, 160, 150))  # Dimmer
        
        metrics = painter.fontMetrics()
        date_width = metrics.horizontalAdvance(date_str)
        painter.drawText(clock_x - date_width // 2, clock_y + 30, date_str)
    
    def _draw_mic_icon(self, painter, w):
        """Draw mic icon at top-right."""
        mic_x = w - 50
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
    
    def _draw_photo_area(self, painter, split_x, w, h):
        """Draw photo area on right side (60%)."""
        # Photo area fills most of right side
        padding = 30
        photo_x = split_x + padding
        photo_y = padding + 60  # Below mic
        photo_w = w - split_x - padding * 2
        photo_h = h - padding * 2 - 60 - 60  # Leave space for mic and menu button
        
        # No border - photos display directly
        
        # Try to draw current photo
        photo_path = self.app_state.get_current_photo_path() if hasattr(self.app_state, 'get_current_photo_path') else None
        
        if photo_path:
            try:
                pixmap = QPixmap(photo_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(photo_w, photo_h, 
                                          Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    px = photo_x + (photo_w - scaled.width()) // 2
                    py = photo_y + (photo_h - scaled.height()) // 2
                    painter.drawPixmap(px, py, scaled)
                    
                    # Store photo rect for click detection
                    self._photo_rect = QRectF(photo_x, photo_y, photo_w, photo_h)
                    return
            except:
                pass
        
        # Placeholder if no photo
        painter.setPen(QColor(60, 60, 60))
        font = QFont("Courier New", 20)
        painter.setFont(font)
        painter.drawText(photo_x, photo_y, photo_w, photo_h, 
                        Qt.AlignCenter, "[ PHOTOS ]")
        
        # Store photo rect for click detection
        self._photo_rect = QRectF(photo_x, photo_y, photo_w, photo_h)
    
    def _draw_menu_button(self, painter, w, h):
        """Draw Menu button at bottom-right."""
        btn_w = 120
        btn_h = 50
        btn_x = w - btn_w - 30
        btn_y = h - btn_h - 30
        
        # Button background
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(btn_x, btn_y, btn_w, btn_h)
        
        # Button text
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Courier New", 18, QFont.Bold)
        painter.setFont(font)
        painter.drawText(btn_x, btn_y, btn_w, btn_h, Qt.AlignCenter, "MENU")
        
        # Store button rect for click detection
        self._menu_rect = QRectF(btn_x, btn_y, btn_w, btn_h)
    
    def _draw_transcription(self, painter, w, h):
        """Draw transcription text overlay."""
        # Semi-transparent overlay
        painter.fillRect(0, h - 150, w, 150, QColor(0, 0, 0, 200))
        
        # Transcription text
        painter.setPen(QColor(100, 255, 100))  # Green like active mic
        font = QFont("Courier New", 16, QFont.Bold)
        painter.setFont(font)
        
        # Draw label
        painter.drawText(20, h - 120, "LISTENING:")
        
        # Draw transcribed text
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Courier New", 14)
        painter.setFont(font)
        painter.drawText(20, h - 90, w - 40, 80, 
                        Qt.AlignLeft | Qt.TextWordWrap, 
                        self.transcription_text)
    
    def mousePressEvent(self, event):
        """Handle tap events."""
        pos = event.pos()
        
        # Check if mic icon tapped
        if hasattr(self, '_mic_rect') and self._mic_rect.contains(pos.x(), pos.y()):
            self.mic_enabled = not self.mic_enabled
            logger.info(f"Mic toggled: {self.mic_enabled}")
            
            # Speak "I'm Listening" when activated
            if self.mic_enabled:
                self._speak("I'm listening")
            
            # Notify main window to start/stop voice service
            if self.mic_toggled:
                self.mic_toggled(self.mic_enabled)
            
            self.update()
            return
        
        # Check if Menu button tapped
        if hasattr(self, '_menu_rect') and self._menu_rect.contains(pos.x(), pos.y()):
            self.navigate(AppState.VIEW_MENU)
            return
        
        # Check if photo area tapped - advance to next photo
        if hasattr(self, '_photo_rect') and self._photo_rect.contains(pos.x(), pos.y()):
            self._next_photo()
            return
    
    def _speak(self, text: str):
        """Speak text using TTS."""
        if not TTS_AVAILABLE:
            logger.warning(f"TTS not available, would say: {text}")
            return
        
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    def set_mic_active(self, active: bool):
        """Set mic active state (called by voice service)."""
        self.mic_enabled = active
        self.update()
    
    def show_transcription(self, text: str):
        """Display transcription text."""
        self.transcription_text = text
        self.show_transcription = True
        self.update()
    
    def clear_transcription(self):
        """Clear transcription text."""
        self.transcription_text = ''
        self.show_transcription = False
        self.update()
    
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
