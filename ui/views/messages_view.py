"""
Messages View
Display and manage messages sent to the smart frame.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame)
from PyQt5.QtGui import QFont

from models.app_state import AppState

logger = logging.getLogger(__name__)


class MessageCard(QFrame):
    """Individual message card widget."""
    
    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Message content
        content_label = QLabel(self.message_data.get('text', ''))
        content_label.setWordWrap(True)
        content_label.setStyleSheet("""
            color: #fff;
            font-size: 18px;
            font-weight: 500;
        """)
        layout.addWidget(content_label)
        
        # Timestamp
        timestamp = self.message_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                time_str = timestamp
        else:
            time_str = "Unknown time"
        
        time_label = QLabel(time_str)
        time_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
        """)
        time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(time_label)


class MessagesView(QWidget):
    """
    Messages view showing all received messages.
    """
    
    closed = pyqtSignal()
    
    def __init__(self, app_state: AppState, navigate_callback=None):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self.messages_file = Path("messages/message_history.json")
        
        self._init_ui()
        self._load_messages()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Set dark background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e,
                    stop:0.5 #16213e,
                    stop:1 #0f3460
                );
            }
        """)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.3);
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Title
        title = QLabel("💬 Messages")
        title.setStyleSheet("""
            color: #fff;
            font-size: 28px;
            font-weight: bold;
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(50, 50)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
                font-size: 24px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        close_btn.clicked.connect(self._close)
        close_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # Scrollable message list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
            }
        """)
        
        # Container for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(30, 20, 30, 20)
        self.messages_layout.setSpacing(15)
        self.messages_layout.setAlignment(Qt.AlignTop)
        
        # Empty state label
        self.empty_label = QLabel("📭\n\nNo messages yet")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.5);
            font-size: 24px;
            padding: 100px;
        """)
        self.messages_layout.addWidget(self.empty_label)
        
        scroll.setWidget(self.messages_container)
        layout.addWidget(scroll)
    
    def _load_messages(self):
        """Load messages from file."""
        # Clear existing messages
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        messages = []
        
        if self.messages_file.exists():
            try:
                with open(self.messages_file, 'r') as f:
                    data = json.load(f)
                    messages = data.get('messages', [])
            except Exception as e:
                logger.error(f"Failed to load messages: {e}")
        
        if not messages:
            # Show empty state
            self.empty_label = QLabel("📭\n\nNo messages yet")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.5);
                font-size: 24px;
                padding: 100px;
            """)
            self.messages_layout.addWidget(self.empty_label)
        else:
            # Show messages (newest first)
            for msg in reversed(messages):
                card = MessageCard(msg)
                self.messages_layout.addWidget(card)
            
            self.messages_layout.addStretch()
    
    def _close(self):
        """Close messages view."""
        self.closed.emit()
        if self.navigate:
            self.navigate(AppState.VIEW_HOME)
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Messages view activated")
        self._load_messages()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Messages view deactivated")
