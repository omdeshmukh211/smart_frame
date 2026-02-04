"""
Photo View
Fullscreen photo slideshow with controls.
"""

import logging
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGraphicsOpacityEffect)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QSize

from models.app_state import AppState
from services.photo_service import PhotoService

logger = logging.getLogger(__name__)


class PhotoView(QWidget):
    """
    Photo slideshow view.
    Displays photos with fade transitions and manual controls.
    """
    
    def __init__(self, app_state: AppState, photo_service: PhotoService, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.photo_service = photo_service
        self.navigate = navigate_callback
        self.current_pixmap = None
        self._init_ui()
        
        # Slideshow timer
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self._next_photo)
        
        # Listen for photo updates
        app_state.register_callback('photo_changed', self._on_photo_changed)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar with close button
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)
        top_bar_layout.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(50, 50)
        self.close_btn.setFont(QFont("Arial", 20, QFont.Bold))
        self.close_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_HOME))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 25px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        top_bar_layout.addWidget(self.close_btn)
        layout.addWidget(top_bar)
        
        # Photo display (main content)
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setScaledContents(False)
        self.photo_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.photo_label, stretch=1)
        
        # Control bar at bottom
        control_bar = QWidget()
        control_bar.setMaximumHeight(80)
        control_bar.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(20, 10, 20, 10)
        
        # Home button
        self.home_btn = self._create_control_button("🏠 Home")
        self.home_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_HOME))
        control_layout.addWidget(self.home_btn)
        
        control_layout.addStretch()
        
        # Previous button
        self.prev_btn = self._create_control_button("⏮ Previous")
        self.prev_btn.clicked.connect(self._previous_photo)
        control_layout.addWidget(self.prev_btn)
        
        # Play/Pause button
        self.play_pause_btn = self._create_control_button("⏸ Pause")
        self.play_pause_btn.clicked.connect(self._toggle_slideshow)
        control_layout.addWidget(self.play_pause_btn)
        
        # Next button
        self.next_btn = self._create_control_button("⏭ Next")
        self.next_btn.clicked.connect(self._next_photo)
        control_layout.addWidget(self.next_btn)
        
        layout.addWidget(control_bar)
        
        # Opacity effect for fade transitions
        self.opacity_effect = QGraphicsOpacityEffect()
        self.photo_label.setGraphicsEffect(self.opacity_effect)
    
    def _create_control_button(self, text: str) -> QPushButton:
        """Create a control button."""
        btn = QPushButton(text)
        btn.setMinimumHeight(60)
        btn.setMinimumWidth(150)
        
        font = QFont("Arial", 14, QFont.Bold)
        btn.setFont(font)
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 10px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        
        return btn
    
    def _load_photo(self):
        """Load and display current photo."""
        photo_path = self.photo_service.get_current_photo_path()
        if not photo_path or not photo_path.exists():
            self.photo_label.setText("No photos available")
            self.photo_label.setStyleSheet("color: white; font-size: 24px;")
            return
        
        try:
            # Load pixmap
            pixmap = QPixmap(str(photo_path))
            if pixmap.isNull():
                logger.warning(f"Failed to load image: {photo_path}")
                return
            
            # Scale to fit screen while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.current_pixmap = scaled_pixmap
            self.photo_label.setPixmap(scaled_pixmap)
            
            # Fade in effect
            self._fade_in()
            
        except Exception as e:
            logger.error(f"Error loading photo: {e}")
    
    def _fade_in(self):
        """Animate fade-in effect."""
        if self.app_state.get_setting('slideshow_transition') == 'fade':
            anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            anim.setDuration(500)  # 500ms fade
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            anim.start()
    
    def _next_photo(self):
        """Go to next photo."""
        self.photo_service.next_photo()
    
    def _previous_photo(self):
        """Go to previous photo."""
        self.photo_service.previous_photo()
    
    def _toggle_slideshow(self):
        """Toggle slideshow play/pause."""
        if self.slideshow_timer.isActive():
            self.slideshow_timer.stop()
            self.play_pause_btn.setText("▶ Play")
        else:
            interval = self.app_state.get_setting('slideshow_interval', 5) * 1000
            self.slideshow_timer.start(interval)
            self.play_pause_btn.setText("⏸ Pause")
    
    def _on_photo_changed(self, index):
        """Handle photo change from service."""
        self._load_photo()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Photo view activated")
        
        # Start slideshow
        interval = self.app_state.get_setting('slideshow_interval', 5) * 1000
        self.slideshow_timer.start(interval)
        self.play_pause_btn.setText("⏸ Pause")
        
        # Load current photo
        self._load_photo()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Photo view deactivated")
        self.slideshow_timer.stop()
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        # Reload photo to fit new size
        if self.current_pixmap:
            self._load_photo()
