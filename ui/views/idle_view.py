"""
Idle View - Robot Face Screen
Displays animated robot face with blinking, yawning, and sleep modes.
"""

import logging
import random
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from models.app_state import AppState

logger = logging.getLogger(__name__)


class IdleView(QWidget):
    """
    Idle screen with animated robot face.
    Shows different expressions: normal, blinking, yawning, sleeping.
    """
    
    # Robot states
    STATE_NORMAL = 'normal'
    STATE_BLINK = 'blink'
    STATE_YAWN = 'yawn'
    STATE_SLEEP = 'sleep'
    STATE_HAPPY = 'happy'
    
    def __init__(self, app_state: AppState, wake_callback):
        super().__init__()
        self.app_state = app_state
        self.wake_callback = wake_callback
        
        self.robot_state = self.STATE_NORMAL
        self.eye_scale = 1.0
        self.float_offset = 0
        self.zzz_opacity = 0
        self.zzz_index = 0
        
        self._init_ui()
        self._init_timers()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Set dark background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a12,
                    stop:0.5 #12121f,
                    stop:1 #0a0a12
                );
            }
        """)
        
        # "Tap to wake" label
        self.wake_label = QLabel("Tap to wake")
        self.wake_label.setAlignment(Qt.AlignCenter)
        self.wake_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.4);
                font-size: 18px;
                background: transparent;
                padding: 20px;
            }
        """)
        
        layout.addStretch()
        layout.addWidget(self.wake_label)
        
        # Click to wake
        self.setCursor(Qt.PointingHandCursor)
    
    def _init_timers(self):
        """Initialize animation timers."""
        # Blink timer - random intervals
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._trigger_blink)
        
        # Yawn timer - every 20 minutes
        self.yawn_timer = QTimer()
        self.yawn_timer.timeout.connect(self._trigger_yawn)
        self.yawn_timer.start(20 * 60 * 1000)  # 20 minutes
        
        # Happy timer - every 5 minutes
        self.happy_timer = QTimer()
        self.happy_timer.timeout.connect(self._trigger_happy)
        self.happy_timer.start(5 * 60 * 1000)  # 5 minutes
        
        # Float animation
        self.float_timer = QTimer()
        self.float_timer.timeout.connect(self._update_float)
        self.float_timer.start(50)  # 20 FPS
        
        # ZZZ animation (when sleeping)
        self.zzz_timer = QTimer()
        self.zzz_timer.timeout.connect(self._update_zzz)
    
    def _schedule_next_blink(self):
        """Schedule next blink at random interval."""
        interval = random.randint(3000, 6000)  # 3-6 seconds
        self.blink_timer.start(interval)
    
    def _trigger_blink(self):
        """Trigger blink animation."""
        if self.robot_state == self.STATE_NORMAL:
            self.robot_state = self.STATE_BLINK
            self.eye_scale = 0.1
            
            # Return to normal after 150ms
            QTimer.singleShot(150, lambda: self._end_blink())
            
        self._schedule_next_blink()
    
    def _end_blink(self):
        """End blink animation."""
        if self.robot_state == self.STATE_BLINK:
            self.robot_state = self.STATE_NORMAL
            self.eye_scale = 1.0
            self.update()
    
    def _trigger_yawn(self):
        """Trigger yawn animation (4 seconds)."""
        if self.robot_state == self.STATE_NORMAL:
            self.robot_state = self.STATE_YAWN
            self.update()
            
            # Return to normal after 4 seconds
            QTimer.singleShot(4000, lambda: self._end_yawn())
    
    def _end_yawn(self):
        """End yawn animation."""
        if self.robot_state == self.STATE_YAWN:
            self.robot_state = self.STATE_NORMAL
            self.update()
    
    def _trigger_happy(self):
        """Trigger happy face (3 seconds)."""
        if self.robot_state == self.STATE_NORMAL:
            self.robot_state = self.STATE_HAPPY
            self.update()
            
            QTimer.singleShot(3000, lambda: self._end_happy())
    
    def _end_happy(self):
        """End happy animation."""
        if self.robot_state == self.STATE_HAPPY:
            self.robot_state = self.STATE_NORMAL
            self.update()
    
    def _update_float(self):
        """Update floating animation."""
        import math
        self.float_offset = math.sin(QTimer().singleShot.__self__.elapsed() / 1000.0) * 6
        self.update()
    
    def _update_zzz(self):
        """Update ZZZ animation for sleep mode."""
        self.zzz_index = (self.zzz_index + 1) % 3
        self.update()
    
    def _check_sleep_mode(self):
        """Check if it's sleep hours (11 PM - 8 AM)."""
        hour = datetime.now().hour
        return hour >= 23 or hour < 8
    
    def paintEvent(self, event):
        """Paint the robot face."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Check if sleep mode
        is_sleep_time = self._check_sleep_mode()
        if is_sleep_time and self.robot_state == self.STATE_NORMAL:
            self.robot_state = self.STATE_SLEEP
            self.zzz_timer.start(2500)
        elif not is_sleep_time and self.robot_state == self.STATE_SLEEP:
            self.robot_state = self.STATE_NORMAL
            self.zzz_timer.stop()
        
        # Center of screen
        center_x = self.width() // 2
        center_y = self.height() // 2 - 50 + int(self.float_offset)
        
        # Draw robot face container
        face_width = 240
        face_height = 180
        face_rect = QRect(
            center_x - face_width // 2,
            center_y - face_height // 2,
            face_width,
            face_height
        )
        
        # Face background (screen-like)
        painter.setPen(Qt.NoPen)
        gradient = QColor(26, 42, 58)  # Dark blue-gray
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(face_rect, 35, 35)
        
        # Glow effect
        glow_color = QColor(100, 180, 255, 25)
        if self.robot_state == self.STATE_SLEEP:
            glow_color = QColor(100, 180, 255, 10)
        painter.setPen(QPen(glow_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(face_rect.adjusted(-3, -3, 3, 3), 38, 38)
        
        # Draw eyes
        self._draw_eyes(painter, center_x, center_y)
        
        # Draw mouth
        self._draw_mouth(painter, center_x, center_y)
        
        # Draw ZZZ if sleeping
        if self.robot_state == self.STATE_SLEEP:
            self._draw_zzz(painter, center_x + 150, center_y - 80)
    
    def _draw_eyes(self, painter, center_x, center_y):
        """Draw robot eyes based on state."""
        eye_y = center_y - 30
        eye_spacing = 50
        
        if self.robot_state == self.STATE_NORMAL or self.robot_state == self.STATE_BLINK:
            # Normal round eyes
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            
            # Left eye
            painter.drawEllipse(
                center_x - eye_spacing - 20,
                int(eye_y - 20 * self.eye_scale),
                40,
                int(40 * self.eye_scale)
            )
            
            # Right eye
            painter.drawEllipse(
                center_x + eye_spacing - 20,
                int(eye_y - 20 * self.eye_scale),
                40,
                int(40 * self.eye_scale)
            )
        
        elif self.robot_state == self.STATE_HAPPY:
            # Happy ^^ eyes
            painter.setPen(QPen(QColor(255, 255, 255), 4, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            
            # Left eye ^
            path_left = QPainterPath()
            path_left.moveTo(center_x - eye_spacing - 13, eye_y + 5)
            path_left.quadTo(
                center_x - eye_spacing, eye_y - 10,
                center_x - eye_spacing + 13, eye_y + 5
            )
            painter.drawPath(path_left)
            
            # Right eye ^
            path_right = QPainterPath()
            path_right.moveTo(center_x + eye_spacing - 13, eye_y + 5)
            path_right.quadTo(
                center_x + eye_spacing, eye_y - 10,
                center_x + eye_spacing + 13, eye_y + 5
            )
            painter.drawPath(path_right)
        
        elif self.robot_state == self.STATE_SLEEP:
            # Sleep -- eyes (lines)
            painter.setPen(QPen(QColor(255, 255, 255), 5, Qt.SolidLine, Qt.RoundCap))
            
            # Left eye
            painter.drawLine(
                center_x - eye_spacing - 14, eye_y,
                center_x - eye_spacing + 14, eye_y
            )
            
            # Right eye
            painter.drawLine(
                center_x + eye_spacing - 14, eye_y,
                center_x + eye_spacing + 14, eye_y
            )
        
        elif self.robot_state == self.STATE_YAWN:
            # Squinting eyes
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            
            # Left eye (squinted)
            painter.drawEllipse(
                center_x - eye_spacing - 20,
                eye_y - 8,
                40,
                16
            )
            
            # Right eye (squinted)
            painter.drawEllipse(
                center_x + eye_spacing - 20,
                eye_y - 8,
                40,
                16
            )
    
    def _draw_mouth(self, painter, center_x, center_y):
        """Draw robot mouth based on state."""
        mouth_y = center_y + 40
        
        painter.setPen(QPen(QColor(255, 255, 255), 4, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        if self.robot_state == self.STATE_YAWN:
            # Yawn mouth (O shape)
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.drawEllipse(center_x - 14, mouth_y - 12, 28, 35)
        
        elif self.robot_state == self.STATE_SLEEP:
            # Small sleep smile
            path = QPainterPath()
            path.moveTo(center_x - 15, mouth_y)
            path.quadTo(center_x, mouth_y + 8, center_x + 15, mouth_y)
            painter.drawPath(path)
        
        else:
            # Normal smile
            path = QPainterPath()
            path.moveTo(center_x - 25, mouth_y - 5)
            path.quadTo(center_x, mouth_y + 15, center_x + 25, mouth_y - 5)
            painter.drawPath(path)
    
    def _draw_zzz(self, painter, x, y):
        """Draw ZZZ animation for sleep mode."""
        painter.setPen(Qt.NoPen)
        
        # Draw 3 Z's with staggered animation
        z_positions = [
            (x, y, 16, 0.3),
            (x + 15, y - 20, 20, 0.5),
            (x + 30, y - 45, 24, 0.7)
        ]
        
        font = QFont("Comic Sans MS", 16)
        font.setItalic(True)
        font.setBold(True)
        
        for i, (zx, zy, size, base_opacity) in enumerate(z_positions):
            # Animated opacity based on zzz_index
            opacity = 0
            if i == self.zzz_index:
                opacity = int(255 * base_opacity)
            
            color = QColor(150, 200, 255, opacity)
            painter.setPen(color)
            font.setPointSize(size)
            painter.setFont(font)
            painter.drawText(QPoint(zx, zy), "Z" if i == 2 else "z")
    
    def mousePressEvent(self, event):
        """Handle mouse/touch to wake."""
        logger.info("Idle view tapped - waking up")
        self.wake_callback()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Idle view activated")
        self._schedule_next_blink()
        self.float_timer.start(50)
        self.update()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Idle view deactivated")
        self.blink_timer.stop()
        self.yawn_timer.stop()
        self.happy_timer.stop()
        self.float_timer.stop()
        self.zzz_timer.stop()
