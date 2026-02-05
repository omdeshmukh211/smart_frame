"""
Idle View - Retro Hardware Style
Simple robot face with two eyes and one mouth.
Frame-based expressions: Awake, Blink, Yawn, Sleep.
"""

import logging
import random
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath

from models.app_state import AppState

logger = logging.getLogger(__name__)


class IdleView(QWidget):
    """
    Idle screen with minimal robot face.
    Pure black background with white eyes and mouth.
    No text, no borders, no icons.
    """
    
    # Expression states (frame-based)
    STATE_AWAKE = 'awake'      # Eyes open
    STATE_BLINK = 'blink'      # Eyes closed briefly
    STATE_YAWN = 'yawn'        # Yawning expression
    STATE_SLEEP = 'sleep'      # Eyes closed (lines)
    
    def __init__(self, app_state: AppState, wake_callback):
        super().__init__()
        self.app_state = app_state
        self.wake_callback = wake_callback
        
        self.expression = self.STATE_AWAKE
        self._init_ui()
        self._init_timers()
    
    def _init_ui(self):
        """Initialize UI - pure black background."""
        self.setStyleSheet("background-color: #000000;")
        self.setCursor(Qt.BlankCursor)
    
    def _init_timers(self):
        """Initialize expression timers."""
        # Blink timer - random intervals
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._trigger_blink)
        
        # Expression cycle timer - slow cycling when idle
        self.cycle_timer = QTimer()
        self.cycle_timer.timeout.connect(self._cycle_expression)
        self.cycle_timer.start(15000)  # Check every 15 seconds
        
        # Repaint timer
        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(100)  # 10 FPS is enough
    
    def _schedule_next_blink(self):
        """Schedule next blink at random interval."""
        interval = random.randint(4000, 8000)  # 4-8 seconds
        self.blink_timer.start(interval)
    
    def _trigger_blink(self):
        """Trigger blink (frame swap)."""
        if self.expression == self.STATE_AWAKE:
            self.expression = self.STATE_BLINK
            self.update()
            # Return to awake after 150ms
            QTimer.singleShot(150, self._end_blink)
        self._schedule_next_blink()
    
    def _end_blink(self):
        """End blink."""
        if self.expression == self.STATE_BLINK:
            self.expression = self.STATE_AWAKE
            self.update()
    
    def _cycle_expression(self):
        """Cycle expressions slowly when idle."""
        # Check for sleep hours (11 PM - 8 AM)
        hour = datetime.now().hour
        is_sleep_time = hour >= 23 or hour < 8
        
        if is_sleep_time:
            self.expression = self.STATE_SLEEP
        elif self.expression == self.STATE_SLEEP:
            self.expression = self.STATE_AWAKE
        elif self.expression == self.STATE_AWAKE:
            # Occasionally yawn
            if random.random() < 0.15:  # 15% chance
                self.expression = self.STATE_YAWN
                QTimer.singleShot(3000, self._end_yawn)
        
        self.update()
    
    def _end_yawn(self):
        """End yawn expression."""
        if self.expression == self.STATE_YAWN:
            self.expression = self.STATE_AWAKE
            self.update()
    
    def paintEvent(self, event):
        """Paint the robot face - eyes and mouth only."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center of screen
        cx = self.width() // 2
        cy = self.height() // 2
        
        # Draw based on expression
        if self.expression == self.STATE_AWAKE:
            self._draw_eyes_open(painter, cx, cy)
            self._draw_mouth_neutral(painter, cx, cy)
        elif self.expression == self.STATE_BLINK:
            self._draw_eyes_closed(painter, cx, cy)
            self._draw_mouth_neutral(painter, cx, cy)
        elif self.expression == self.STATE_YAWN:
            self._draw_eyes_squint(painter, cx, cy)
            self._draw_mouth_yawn(painter, cx, cy)
        elif self.expression == self.STATE_SLEEP:
            self._draw_eyes_sleep(painter, cx, cy)
            self._draw_mouth_sleep(painter, cx, cy)
    
    def _draw_eyes_open(self, painter, cx, cy):
        """Draw open eyes - two white ellipses."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(240, 240, 230)))  # Off-white
        
        eye_y = cy - 40
        eye_spacing = 60
        eye_w, eye_h = 50, 60
        
        # Left eye
        painter.drawEllipse(cx - eye_spacing - eye_w//2, eye_y - eye_h//2, eye_w, eye_h)
        # Right eye
        painter.drawEllipse(cx + eye_spacing - eye_w//2, eye_y - eye_h//2, eye_w, eye_h)
    
    def _draw_eyes_closed(self, painter, cx, cy):
        """Draw closed eyes (blink) - horizontal lines."""
        painter.setPen(QPen(QColor(240, 240, 230), 6, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        eye_y = cy - 40
        eye_spacing = 60
        line_w = 25
        
        # Left eye line
        painter.drawLine(cx - eye_spacing - line_w, eye_y, cx - eye_spacing + line_w, eye_y)
        # Right eye line
        painter.drawLine(cx + eye_spacing - line_w, eye_y, cx + eye_spacing + line_w, eye_y)
    
    def _draw_eyes_squint(self, painter, cx, cy):
        """Draw squinting eyes - narrow ellipses."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(240, 240, 230)))
        
        eye_y = cy - 40
        eye_spacing = 60
        eye_w, eye_h = 50, 20  # Squinted
        
        # Left eye
        painter.drawEllipse(cx - eye_spacing - eye_w//2, eye_y - eye_h//2, eye_w, eye_h)
        # Right eye
        painter.drawEllipse(cx + eye_spacing - eye_w//2, eye_y - eye_h//2, eye_w, eye_h)
    
    def _draw_eyes_sleep(self, painter, cx, cy):
        """Draw sleeping eyes - closed lines."""
        painter.setPen(QPen(QColor(240, 240, 230), 5, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        eye_y = cy - 40
        eye_spacing = 60
        line_w = 20
        
        # Left eye - slightly curved downward
        painter.drawLine(cx - eye_spacing - line_w, eye_y, cx - eye_spacing + line_w, eye_y)
        # Right eye
        painter.drawLine(cx + eye_spacing - line_w, eye_y, cx + eye_spacing + line_w, eye_y)
    
    def _draw_mouth_neutral(self, painter, cx, cy):
        """Draw neutral mouth - simple line with slight curve."""
        painter.setPen(QPen(QColor(240, 240, 230), 4, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        mouth_y = cy + 50
        mouth_w = 40
        
        path = QPainterPath()
        path.moveTo(cx - mouth_w, mouth_y)
        path.quadTo(cx, mouth_y + 10, cx + mouth_w, mouth_y)
        painter.drawPath(path)
    
    def _draw_mouth_yawn(self, painter, cx, cy):
        """Draw yawning mouth - open ellipse."""
        painter.setPen(QPen(QColor(240, 240, 230), 3))
        painter.setBrush(QBrush(QColor(20, 20, 20)))  # Dark inside
        
        mouth_y = cy + 50
        painter.drawEllipse(cx - 20, mouth_y - 15, 40, 45)
    
    def _draw_mouth_sleep(self, painter, cx, cy):
        """Draw sleeping mouth - small smile."""
        painter.setPen(QPen(QColor(240, 240, 230), 3, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        mouth_y = cy + 50
        mouth_w = 20
        
        path = QPainterPath()
        path.moveTo(cx - mouth_w, mouth_y)
        path.quadTo(cx, mouth_y + 6, cx + mouth_w, mouth_y)
        painter.drawPath(path)
    
    def mousePressEvent(self, event):
        """Handle touch - wake up."""
        logger.info("Idle view tapped - waking up")
        self.wake_callback()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Idle view activated")
        self.expression = self.STATE_AWAKE
        self._cycle_expression()  # Check if should be sleeping
        self._schedule_next_blink()
        self.repaint_timer.start(100)
        self.update()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Idle view deactivated")
        self.blink_timer.stop()
        self.repaint_timer.stop()
