"""
Messages View - Retro Hardware Style
Text-based message list with arrow selection.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtGui import QFont, QKeyEvent, QPainter, QColor

from models.app_state import AppState

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class MessagesView(QWidget):
    """
    Messages view - Retro Hardware Style.
    
    MESSAGES LIST:
    ▶ 07:30 Drink Water
      09:00 Stand Up
      13:00 Meeting
    
    - List only, one-line summaries
    - Unread messages visually marked
    - Select to view detail
    """
    
    def __init__(self, app_state: AppState, navigate_callback=None):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self.messages_file = Path("messages/message_history.json")
        
        self.messages = []
        self.selected_index = 0
        self.viewing_detail = False
        self.current_message = None
        
        self._init_ui()
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setStyleSheet("background-color: #000000;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)
        
        # Title
        self.title_label = QLabel("MESSAGES")
        self.title_label.setFont(QFont("Courier New", 32, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0; background: transparent;")
        self.title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title_label)
        
        layout.addSpacing(30)
        
        # Separator
        self.separator = QLabel("─" * 50)
        self.separator.setFont(QFont("Courier New", 14))
        self.separator.setStyleSheet("color: #404040; background: transparent;")
        layout.addWidget(self.separator)
        
        layout.addSpacing(20)
        
        # Message list container
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        
        # Placeholder for message labels
        self.message_labels = []
        
        layout.addWidget(self.list_container)
        layout.addStretch()
        
        # Detail view (hidden by default)
        self.detail_container = QWidget()
        self.detail_container.setStyleSheet("background: transparent;")
        self.detail_container.hide()
        detail_layout = QVBoxLayout(self.detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(15)
        
        self.detail_time = QLabel()
        self.detail_time.setFont(QFont("Courier New", 14))
        self.detail_time.setStyleSheet("color: #808080; background: transparent;")
        detail_layout.addWidget(self.detail_time)
        
        self.detail_title = QLabel()
        self.detail_title.setFont(QFont("Courier New", 24, QFont.Bold))
        self.detail_title.setStyleSheet("color: #E0E0E0; background: transparent;")
        self.detail_title.setWordWrap(True)
        detail_layout.addWidget(self.detail_title)
        
        self.detail_body = QLabel()
        self.detail_body.setFont(QFont("Courier New", 16))
        self.detail_body.setStyleSheet("color: #C0C0C0; background: transparent;")
        self.detail_body.setWordWrap(True)
        detail_layout.addWidget(self.detail_body)
        
        detail_layout.addStretch()
        layout.addWidget(self.detail_container)
        
        # Hint at bottom
        self.hint_label = QLabel("[TAP] View   [BACK] Menu")
        self.hint_label.setFont(QFont("Courier New", 14))
        self.hint_label.setStyleSheet("color: #606060; background: transparent;")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        # Empty state
        self.empty_label = QLabel("No messages")
        self.empty_label.setFont(QFont("Courier New", 18))
        self.empty_label.setStyleSheet("color: #606060; background: transparent;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.hide()
        self.list_layout.addWidget(self.empty_label)
    
    def _load_messages(self):
        """Load messages from file."""
        self.messages = []
        
        try:
            if self.messages_file.exists():
                with open(self.messages_file, 'r') as f:
                    data = json.load(f)
                    self.messages = data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to load messages: {e}")
        
        self._update_display()
    
    def _update_display(self):
        """Update the message list display."""
        # Clear existing labels
        for label in self.message_labels:
            label.deleteLater()
        self.message_labels = []
        
        if not self.messages:
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        
        for i, msg in enumerate(self.messages[:15]):  # Show max 15
            label = QLabel()
            label.setFont(QFont("Courier New", 18))
            label.setCursor(Qt.PointingHandCursor)
            label.mousePressEvent = lambda e, idx=i: self._select_message(idx)
            
            # Format: "▶ HH:MM Title" or "  HH:MM Title"
            timestamp = msg.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "??:??"
            
            title = msg.get('title', msg.get('text', 'Message'))
            if len(title) > 40:
                title = title[:37] + "..."
            
            # Check if unread
            is_unread = not msg.get('read', True)
            
            if i == self.selected_index:
                text = f"▶ {time_str} {title}"
                style = "color: #FFFFFF; background: transparent;"
            else:
                text = f"  {time_str} {title}"
                if is_unread:
                    style = "color: #90FF90; background: transparent;"  # Green for unread
                else:
                    style = "color: #808080; background: transparent;"
            
            label.setText(text)
            label.setStyleSheet(style)
            
            self.message_labels.append(label)
            self.list_layout.addWidget(label)
    
    def _select_message(self, index: int):
        """Select and view a message."""
        self.selected_index = index
        self._update_display()
        QTimer.singleShot(100, self._show_detail)
    
    def _show_detail(self):
        """Show message detail view."""
        if self.selected_index >= len(self.messages):
            return
        
        msg = self.messages[self.selected_index]
        self.current_message = msg
        self.viewing_detail = True
        
        # Update detail labels
        timestamp = msg.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%a %d %b %Y at %H:%M")
        except:
            time_str = timestamp
        
        self.detail_time.setText(time_str)
        self.detail_title.setText(msg.get('title', 'Message'))
        self.detail_body.setText(msg.get('text', msg.get('body', '')))
        
        # Mark as read
        msg['read'] = True
        self._save_messages()
        
        # Switch to detail view
        self.list_container.hide()
        self.detail_container.show()
        self.title_label.setText("MESSAGE")
        self.hint_label.setText("[BACK] Return to list")
        
        self.update()
    
    def _show_list(self):
        """Return to message list."""
        self.viewing_detail = False
        self.current_message = None
        
        self.detail_container.hide()
        self.list_container.show()
        self.title_label.setText("MESSAGES")
        self.hint_label.setText("[TAP] View   [BACK] Menu")
        
        self._update_display()
    
    def _save_messages(self):
        """Save messages to file."""
        try:
            self.messages_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.messages_file, 'w') as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        key = event.key()
        
        if self.viewing_detail:
            if key == Qt.Key_Escape or key == Qt.Key_Backspace:
                self._show_list()
            return
        
        if key == Qt.Key_Up:
            if self.messages:
                self.selected_index = (self.selected_index - 1) % len(self.messages)
                self._update_display()
        elif key == Qt.Key_Down:
            if self.messages:
                self.selected_index = (self.selected_index + 1) % len(self.messages)
                self._update_display()
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            if self.messages:
                self._show_detail()
        elif key == Qt.Key_Escape:
            self._go_back()
        else:
            super().keyPressEvent(event)
    
    def _go_back(self):
        """Go back to menu."""
        if self.viewing_detail:
            self._show_list()
        elif self.navigate:
            self.navigate(AppState.VIEW_MENU)
    
    def mousePressEvent(self, event):
        """Handle tap outside message items."""
        # Check if clicked on a message label
        for i, label in enumerate(self.message_labels):
            if label.geometry().contains(event.pos()):
                return  # Let the label handle it
        
        # Tap outside goes back
        self._go_back()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Messages view activated")
        self.selected_index = 0
        self.viewing_detail = False
        self._load_messages()
        self._show_list()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Messages view deactivated")
