"""
Games View - Retro Hardware Style
Text-based game list with arrow selection.
"""

import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QKeyEvent

from models.app_state import AppState

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class GamesView(QWidget):
    """
    Games list screen - Retro Hardware Style.
    
    GAMES LIST:
    ▶ Snake
      X-O
      Wordle
    
    - Selecting a game opens it full-screen
    - Back returns to Menu
    """
    
    GAME_ITEMS = [
        ('Snake', 'snake'),
        ('X-O', 'tictactoe'),
        ('Wordle', 'wordle'),
    ]
    
    def __init__(self, app_state: AppState, navigate_callback=None):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self.selected_index = 0
        self.current_game = None
        
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
        self.title_label = QLabel("GAMES")
        self.title_label.setFont(QFont("Courier New", 32, QFont.Bold))
        self.title_label.setStyleSheet("color: #E0E0E0; background: transparent;")
        self.title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title_label)
        
        layout.addSpacing(40)
        
        # Game list
        self.game_labels = []
        for i, (name, _) in enumerate(self.GAME_ITEMS):
            label = QLabel()
            label.setFont(QFont("Courier New", 24))
            label.setStyleSheet("color: #E0E0E0; background: transparent;")
            label.setAlignment(Qt.AlignLeft)
            label.setCursor(Qt.PointingHandCursor)
            # Make clickable
            label.mousePressEvent = lambda e, idx=i: self._select_game(idx)
            self.game_labels.append(label)
            layout.addWidget(label)
            layout.addSpacing(20)
        
        layout.addStretch()
        
        # Hint at bottom
        self.hint_label = QLabel("[TAP] Play   [BACK] Menu")
        self.hint_label.setFont(QFont("Courier New", 14))
        self.hint_label.setStyleSheet("color: #606060; background: transparent;")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        self._update_display()
    
    def _update_display(self):
        """Update display with selection indicator."""
        for i, (name, _) in enumerate(self.GAME_ITEMS):
            if i == self.selected_index:
                self.game_labels[i].setText(f"▶ {name}")
                self.game_labels[i].setStyleSheet("color: #FFFFFF; background: transparent;")
            else:
                self.game_labels[i].setText(f"  {name}")
                self.game_labels[i].setStyleSheet("color: #808080; background: transparent;")
    
    def _select_game(self, index: int):
        """Select and launch game."""
        self.selected_index = index
        self._update_display()
        QTimer.singleShot(100, self._launch_selected_game)
    
    def _launch_selected_game(self):
        """Launch the selected game."""
        _, game_id = self.GAME_ITEMS[self.selected_index]
        logger.info(f"Launching game: {game_id}")
        self.current_game = game_id
        
        # TODO: Implement actual game screens
        # For now, show game placeholder
        self._show_game_placeholder(game_id)
    
    def _show_game_placeholder(self, game_id: str):
        """Show placeholder for game (games would be separate full-screen widgets)."""
        # In a full implementation, this would switch to the actual game widget
        # For now we just log it
        logger.info(f"Game {game_id} would launch here")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        key = event.key()
        
        if key == Qt.Key_Up:
            self.selected_index = (self.selected_index - 1) % len(self.GAME_ITEMS)
            self._update_display()
        elif key == Qt.Key_Down:
            self.selected_index = (self.selected_index + 1) % len(self.GAME_ITEMS)
            self._update_display()
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._launch_selected_game()
        elif key == Qt.Key_Escape:
            self._go_back()
        else:
            super().keyPressEvent(event)
    
    def _go_back(self):
        """Go back to menu."""
        if self.current_game:
            # Exit game, return to games list
            self.current_game = None
            self._update_display()
        elif self.navigate:
            self.navigate(AppState.VIEW_MENU)
    
    def mousePressEvent(self, event):
        """Handle tap outside game items - go back."""
        if not any(label.geometry().contains(event.pos()) for label in self.game_labels):
            self._go_back()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Games view activated")
        self.selected_index = 0
        self.current_game = None
        self._update_display()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Games view deactivated")
        self.current_game = None
