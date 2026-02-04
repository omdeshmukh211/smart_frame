"""
Home View
Main landing screen with navigation options.
"""

import logging
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QFont

from models.app_state import AppState

logger = logging.getLogger(__name__)


class HomeView(QWidget):
    """
    Home screen view.
    Shows clock and navigation buttons.
    """
    
    def __init__(self, app_state: AppState, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self._init_ui()
        
        # Clock update timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)  # Update every second
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(30)
        
        # Add spacer at top
        layout.addSpacing(50)
        
        # Clock display
        clock_layout = QVBoxLayout()
        clock_layout.setAlignment(Qt.AlignCenter)
        
        self.time_label = QLabel()
        time_font = QFont("Arial", 72, QFont.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignCenter)
        clock_layout.addWidget(self.time_label)
        
        self.date_label = QLabel()
        date_font = QFont("Arial", 24)
        self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignCenter)
        clock_layout.addWidget(self.date_label)
        
        layout.addLayout(clock_layout)
        
        # Add spacer
        layout.addSpacing(50)
        
        # Navigation buttons
        button_layout = QGridLayout()
        button_layout.setSpacing(20)
        
        # Create large touch-friendly buttons
        self.photo_btn = self._create_nav_button("📷\nPhotos", AppState.VIEW_PHOTOS)
        self.music_btn = self._create_nav_button("🎵\nMusic", AppState.VIEW_MUSIC)
        self.settings_btn = self._create_nav_button("⚙️\nSettings", AppState.VIEW_SETTINGS)
        
        button_layout.addWidget(self.photo_btn, 0, 0)
        button_layout.addWidget(self.music_btn, 0, 1)
        button_layout.addWidget(self.settings_btn, 1, 0, 1, 2)
        
        layout.addLayout(button_layout)
        
        # Add bottom spacer
        layout.addStretch()
        
        # Initial clock update
        self._update_clock()
    
    def _create_nav_button(self, text: str, view: str) -> QPushButton:
        """Create a navigation button."""
        btn = QPushButton(text)
        btn.setMinimumHeight(120)
        btn.setMinimumWidth(200)
        
        # Large, readable font
        font = QFont("Arial", 20, QFont.Bold)
        btn.setFont(font)
        
        # Connect to navigation
        btn.clicked.connect(lambda: self.navigate(view))
        
        # Styling
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                padding: 20px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        
        return btn
    
    def _update_clock(self):
        """Update clock display."""
        now = datetime.now()
        
        # Update time (HH:MM)
        time_str = now.strftime("%H:%M")
        self.time_label.setText(time_str)
        
        # Update date
        date_str = now.strftime("%A, %B %d, %Y")
        self.date_label.setText(date_str)
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Home view activated")
        self.clock_timer.start(1000)
        self._update_clock()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Home view deactivated")
        # Keep timer running as it's lightweight
