"""
Home View
Main landing screen with clock, photo frame, and circular action buttons.
Features day/night mode with sun/moon icons and animated backgrounds.
"""

import logging
import math
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QFrame)
from PyQt5.QtGui import (QFont, QPainter, QPen, QBrush, QColor, QPainterPath,
                        QLinearGradient, QRadialGradient, QPalette, QPixmap)

from models.app_state import AppState

logger = logging.getLogger(__name__)


class CircularButton(QPushButton):
    """Circular button with icon and label below."""
    
    def __init__(self, icon_svg, label_text, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.icon_svg = icon_svg
        self.setFixedSize(120, 110)  # Size for 5 buttons in ~768px width
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
        """)
    
    def paintEvent(self, event):
        """Custom paint for circular button."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circle
        circle_size = 60
        circle_x = (self.width() - circle_size) // 2
        circle_y = 5
        
        # Circle background
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
        painter.drawEllipse(circle_x, circle_y, circle_size, circle_size)
        
        # Draw simple icon (text-based for simplicity)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 24)
        painter.setFont(font)
        painter.drawText(
            circle_x, circle_y, circle_size, circle_size,
            Qt.AlignCenter, self.icon_svg
        )
        
        # Draw label below
        font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            0, circle_y + circle_size + 8,
            self.width(), 25,
            Qt.AlignCenter, self.label_text
        )


class HomeView(QWidget):
    """
    Home screen view with day/night mode.
    Shows clock, sun/moon, photo frame preview, and circular action buttons.
    """
    
    def __init__(self, app_state: AppState, navigate_callback, show_messages_callback=None, show_games_callback=None):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self.show_messages_callback = show_messages_callback
        self.show_games_callback = show_games_callback
        
        self.is_day_mode = True
        self.sun_rotation = 0
        self.stars = []
        self._generate_stars()
        
        self._init_ui()
        
        # Clock update timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        
        # Sun rotation animation
        self.sun_timer = QTimer()
        self.sun_timer.timeout.connect(self._rotate_sun)
        self.sun_timer.start(50)
        
        # Check day/night mode
        self._update_day_night_mode()
    
    def _generate_stars(self):
        """Generate random star positions for night mode."""
        import random
        self.stars = []
        for _ in range(25):
            self.stars.append({
                'x': random.random(),
                'y': random.random(),
                'size': random.choice([2, 3, 4]),
                'twinkle_offset': random.random() * 360
            })
    
    def _init_ui(self):
        """Initialize UI components."""
        # Screen is 1024x600
        # Layout: 40% left (~410px) | 60% right (~614px)
        # Right side: 75% top (photo) = 450px | 25% bottom (buttons) = 150px
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ===== LEFT SIDE (40%) - Clock, Date, Sun/Moon =====
        left_widget = QWidget()
        left_widget.setFixedWidth(410)  # 40% of 1024
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 15, 20)
        left_layout.setSpacing(5)
        
        # Sun/Moon area at top (drawn in paintEvent)
        left_layout.addSpacing(100)
        
        # Clock display
        self.time_label = QLabel()
        time_font = QFont("Arial", 64, QFont.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignLeft)
        left_layout.addWidget(self.time_label)
        
        # Date display
        self.date_label = QLabel()
        date_font = QFont("Arial", 18)
        self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignLeft)
        left_layout.addWidget(self.date_label)
        
        left_layout.addStretch()
        
        # ===== RIGHT SIDE (60%) - Photo Frame + Buttons =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(15, 15, 20, 10)
        right_layout.setSpacing(10)
        
        # ----- Top 75% of right side: Photo Frame (fixed 450px) -----
        self.photo_frame = QFrame()
        self.photo_frame.setFixedHeight(450)  # 75% of 600px
        self.photo_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 15px;
            }
        """)
        
        photo_layout = QVBoxLayout(self.photo_frame)
        photo_layout.setAlignment(Qt.AlignCenter)
        
        self.photo_preview = QLabel("📷")
        self.photo_preview.setAlignment(Qt.AlignCenter)
        photo_font = QFont("Arial", 48)
        self.photo_preview.setFont(photo_font)
        photo_layout.addWidget(self.photo_preview)
        
        photo_text = QLabel("Photo Frame")
        photo_text.setAlignment(Qt.AlignCenter)
        photo_text.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 16px;")
        photo_layout.addWidget(photo_text)
        
        # Make photo frame clickable
        self.photo_frame.mousePressEvent = lambda e: self.navigate(AppState.VIEW_PHOTOS)
        self.photo_frame.setCursor(Qt.PointingHandCursor)
        
        right_layout.addWidget(self.photo_frame)
        
        # ----- Bottom 25% of right side: Buttons (fixed 140px) -----
        buttons_widget = QWidget()
        buttons_widget.setFixedHeight(140)  # ~25% of 600px minus margins
        buttons_widget.setStyleSheet("background: transparent;")
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        # Create circular buttons
        self.music_btn = CircularButton("🎵", "Music")
        self.music_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_MUSIC))
        
        self.sleep_btn = CircularButton("😴", "Sleep")
        self.sleep_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_IDLE))
        
        self.settings_btn = CircularButton("⚙️", "Settings")
        self.settings_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_SETTINGS))
        
        self.games_btn = CircularButton("🎮", "Games")
        if self.show_games_callback:
            self.games_btn.clicked.connect(self.show_games_callback)
        
        self.messages_btn = CircularButton("💬", "Messages")
        if self.show_messages_callback:
            self.messages_btn.clicked.connect(self.show_messages_callback)
        
        buttons_layout.addWidget(self.music_btn)
        buttons_layout.addWidget(self.sleep_btn)
        buttons_layout.addWidget(self.settings_btn)
        buttons_layout.addWidget(self.games_btn)
        buttons_layout.addWidget(self.messages_btn)
        
        right_layout.addWidget(buttons_widget)
        
        # Add left and right to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, stretch=1)
        
        # Initial clock update
        self._update_clock()
    
    def paintEvent(self, event):
        """Custom paint for background and sun/moon."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background gradient
        if self.is_day_mode:
            self._draw_day_background(painter)
            self._draw_sun(painter)
        else:
            self._draw_night_background(painter)
            self._draw_stars(painter)
            self._draw_moon(painter)
    
    def _draw_day_background(self, painter):
        """Draw day mode gradient."""
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#FFF9E6"))
        gradient.setColorAt(0.3, QColor("#FFECB3"))
        gradient.setColorAt(1, QColor("#FFE082"))
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Update text colors for day mode
        self.time_label.setStyleSheet("color: #000;")
        self.date_label.setStyleSheet("color: #333;")
    
    def _draw_night_background(self, painter):
        """Draw night mode gradient."""
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#0a0a1a"))
        gradient.setColorAt(0.5, QColor("#1a1a3a"))
        gradient.setColorAt(1, QColor("#0d0d2b"))
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Update text colors for night mode
        self.time_label.setStyleSheet("color: #fff;")
        self.date_label.setStyleSheet("color: #ccc;")
    
    def _draw_sun(self, painter):
        """Draw animated sun."""
        # Position sun in top-left of the 40% column (410px wide)
        center_x, center_y = 90, 70
        radius = 40
        
        # Sun glow
        glow = QRadialGradient(center_x, center_y, 70)
        glow.setColorAt(0, QColor(255, 215, 0, 255))
        glow.setColorAt(0.6, QColor(255, 165, 0, 150))
        glow.setColorAt(1, QColor(255, 140, 0, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), 70, 70)
        
        # Main sun circle
        painter.setBrush(QBrush(QColor("#FFD700")))
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        
        # Sun rays (rotating)
        painter.setPen(QPen(QColor("#FFD700"), 4, Qt.SolidLine, Qt.RoundCap))
        for i in range(8):
            angle = (i * 45 + self.sun_rotation) * math.pi / 180
            x1 = center_x + radius * 1.3 * math.cos(angle)
            y1 = center_y + radius * 1.3 * math.sin(angle)
            x2 = center_x + radius * 1.7 * math.cos(angle)
            y2 = center_y + radius * 1.7 * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _draw_moon(self, painter):
        """Draw moon."""
        # Position moon in top-left of the 40% column (410px wide)
        center_x, center_y = 90, 70
        
        # Moon glow
        glow = QRadialGradient(center_x, center_y, 65)
        glow.setColorAt(0, QColor(232, 232, 208, 100))
        glow.setColorAt(1, QColor(232, 232, 208, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), 65, 65)
        
        # Main moon (crescent shape)
        painter.setBrush(QBrush(QColor("#F5F5DC")))
        painter.drawEllipse(QPointF(center_x, center_y), 40, 40)
        
        # Dark overlay for crescent
        painter.setBrush(QBrush(self.palette().color(QPalette.Window)))
        painter.drawEllipse(QPointF(center_x + 16, center_y), 35, 35)
        
        # Moon craters
        painter.setBrush(QBrush(QColor("#E8E8D0")))
        painter.setOpacity(0.5)
        painter.drawEllipse(QPointF(center_x - 12, center_y - 5), 6, 6)
        painter.drawEllipse(QPointF(center_x + 4, center_y + 12), 10, 10)
        painter.drawEllipse(QPointF(center_x - 16, center_y + 16), 5, 5)
        painter.setOpacity(1.0)
    
    def _draw_stars(self, painter):
        """Draw twinkling stars."""
        import time
        
        painter.setPen(Qt.NoPen)
        
        for star in self.stars:
            x = star['x'] * self.width()
            y = star['y'] * self.height()
            size = star['size']
            
            # Twinkling effect
            twinkle = (math.sin(time.time() * 2 + star['twinkle_offset']) + 1) / 2
            opacity = int(100 + 155 * twinkle)
            
            painter.setBrush(QBrush(QColor(255, 255, 255, opacity)))
            painter.drawEllipse(QPointF(x, y), size, size)
    
    def _rotate_sun(self):
        """Rotate sun rays."""
        self.sun_rotation = (self.sun_rotation + 1) % 360
        if self.is_day_mode:
            self.update()
    
    def _update_day_night_mode(self):
        """Check and update day/night mode."""
        hour = datetime.now().hour
        was_day = self.is_day_mode
        self.is_day_mode = 6 <= hour < 18
        
        if was_day != self.is_day_mode:
            logger.info(f"Switching to {'day' if self.is_day_mode else 'night'} mode")
            self.update()
    
    def _update_clock(self):
        """Update clock display."""
        now = datetime.now()
        
        # Update time (HH:MM)
        time_str = now.strftime("%H:%M")
        self.time_label.setText(time_str)
        
        # Update date
        date_str = now.strftime("%a %d %b %Y")
        self.date_label.setText(date_str)
        
        # Check day/night mode every minute
        if now.second == 0:
            self._update_day_night_mode()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Home view activated")
        self.clock_timer.start(1000)
        self.sun_timer.start(50)
        self._update_clock()
        self._update_day_night_mode()
        self.update()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Home view deactivated")
        # Keep timers running
