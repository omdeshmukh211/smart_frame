"""
Menu View - Retro Hardware Style
Simple text-based menu with arrow selection.
"""

import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QKeyEvent

from models.app_state import AppState

logger = logging.getLogger(__name__)


class MenuView(QWidget):
    """
    Retro menu screen.
    Text list with arrow indicator for selection.
    """
    
    MENU_ITEMS = [
        ('Games', AppState.VIEW_GAMES),
        ('Music', AppState.VIEW_MUSIC),
        ('Messages', AppState.VIEW_MESSAGES),
        ('Settings', AppState.VIEW_SETTINGS),
    ]
    
    def __init__(self, app_state: AppState, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self.selected_index = 0
        
        self._init_ui()
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _init_ui(self):
        """Initialize UI components."""
        # Pure black background
        self.setStyleSheet("background-color: #000000;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)
        
        # Title
        self.title_label = QLabel("MENU")
        self.title_label.setFont(QFont("Courier New", 32, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0; background: transparent;")
        self.title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title_label)
        
        layout.addSpacing(40)
        
        # Menu items
        self.menu_labels = []
        for i, (name, _) in enumerate(self.MENU_ITEMS):
            label = QLabel()
            label.setFont(QFont("Courier New", 24))
            label.setStyleSheet("color: #E0E0E0; background: transparent;")
            label.setAlignment(Qt.AlignLeft)
            label.setCursor(Qt.PointingHandCursor)
            # Make clickable
            label.mousePressEvent = lambda e, idx=i: self._select_item(idx)
            self.menu_labels.append(label)
            layout.addWidget(label)
            layout.addSpacing(20)
        
        layout.addStretch()
        
        # Hint at bottom
        self.hint_label = QLabel("[TAP] Select   [BACK] Home")
        self.hint_label.setFont(QFont("Courier New", 14))
        self.hint_label.setStyleSheet("color: #606060; background: transparent;")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        self._update_display()
    
    def _update_display(self):
        """Update menu display with selection indicator."""
        for i, (name, _) in enumerate(self.MENU_ITEMS):
            if i == self.selected_index:
                self.menu_labels[i].setText(f"▶ {name}")
                self.menu_labels[i].setStyleSheet("color: #FFFFFF; background: transparent;")
            else:
                self.menu_labels[i].setText(f"  {name}")
                self.menu_labels[i].setStyleSheet("color: #808080; background: transparent;")
    
    def _select_item(self, index: int):
        """Select and navigate to menu item."""
        self.selected_index = index
        self._update_display()
        # Small delay before navigation for visual feedback
        QTimer.singleShot(100, self._navigate_to_selected)
    
    def _navigate_to_selected(self):
        """Navigate to the selected item."""
        _, view_name = self.MENU_ITEMS[self.selected_index]
        logger.info(f"Menu: navigating to {view_name}")
        self.navigate(view_name)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        key = event.key()
        
        if key == Qt.Key_Up:
            self.selected_index = (self.selected_index - 1) % len(self.MENU_ITEMS)
            self._update_display()
        elif key == Qt.Key_Down:
            self.selected_index = (self.selected_index + 1) % len(self.MENU_ITEMS)
            self._update_display()
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._navigate_to_selected()
        elif key == Qt.Key_Escape:
            self.navigate(AppState.VIEW_HOME)
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle tap on empty area - go back to home."""
        # Only if not on a menu item
        if not any(label.geometry().contains(event.pos()) for label in self.menu_labels):
            self.navigate(AppState.VIEW_HOME)
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Menu view activated")
        self.selected_index = 0
        self._update_display()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Menu view deactivated")
