"""
Games View - Retro Hardware Style
Text-based game list with arrow selection.
"""

import logging
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QPushButton
from PyQt5.QtGui import QFont, QKeyEvent

from models.app_state import AppState
from ui.games.snake_game import SnakeGameWidget
from ui.games.tictactoe_game import TicTacToeWidget
from ui.games.wordle_game import WordleWidget

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
        
        # Game widgets
        self.game_widgets = {}
        
        self._init_ui()
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _init_ui(self):
        """Initialize UI components."""
        # Pure black background
        self.setStyleSheet("background-color: #000000;")
        
        # Main stacked widget (list view + game views)
        self.stack = QStackedWidget(self)
        self.stack.setStyleSheet("background-color: #000000;")
        
        # Create list view
        self.list_view = self._create_list_view()
        self.stack.addWidget(self.list_view)
        
        # Create game widgets
        self.game_widgets['snake'] = SnakeGameWidget(self)
        self.game_widgets['snake'].game_over.connect(self._on_game_over)
        self.stack.addWidget(self.game_widgets['snake'])
        
        self.game_widgets['tictactoe'] = TicTacToeWidget(self)
        self.game_widgets['tictactoe'].game_over.connect(self._on_game_over)
        self.stack.addWidget(self.game_widgets['tictactoe'])
        
        self.game_widgets['wordle'] = WordleWidget(self)
        self.game_widgets['wordle'].game_over.connect(self._on_game_over)
        self.stack.addWidget(self.game_widgets['wordle'])
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        
        self.stack.setCurrentWidget(self.list_view)
    
    def _create_list_view(self):
        """Create the game list view."""
        widget = QWidget()
        widget.setStyleSheet("background-color: #000000;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)
        
        # Top bar with close button
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(50, 50)
        self.close_btn.setFont(QFont("Arial", 20, QFont.Bold))
        self.close_btn.clicked.connect(lambda: self._go_back())
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
        layout.addLayout(top_bar_layout)
        
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
        
        self._update_display()
        
        return widget
    
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
        
        # Switch to game widget
        game_widget = self.game_widgets[game_id]
        self.stack.setCurrentWidget(game_widget)
        
        # Activate game
        if hasattr(game_widget, 'on_activate'):
            game_widget.on_activate()
        
        game_widget.setFocus()
    
    def _on_game_over(self, *args):
        """Handle game over event."""
        logger.info(f"Game over: {args}")
        # Game will handle showing results
        # User can press R to restart or Back to exit
    
    def _show_game_placeholder(self, game_id: str):
        """Show placeholder for game (games would be separate full-screen widgets)."""
        # Deprecated - now using actual game widgets
        pass
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        # If we're in a game, pass events to the game widget
        if self.current_game:
            game_widget = self.game_widgets[self.current_game]
            
            # Back key exits game
            if event.key() == Qt.Key_Escape:
                self._go_back()
            else:
                # Pass to game widget
                game_widget.keyPressEvent(event)
            return
        
        # Otherwise handle list navigation
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
            game_widget = self.game_widgets[self.current_game]
            if hasattr(game_widget, 'on_deactivate'):
                game_widget.on_deactivate()
            
            self.current_game = None
            self.stack.setCurrentWidget(self.list_view)
            self._update_display()
        elif self.navigate:
            self.navigate(AppState.VIEW_MENU)
    
    def mousePressEvent(self, event):
        """Handle tap events."""
        # If in a game, pass to game widget
        if self.current_game:
            game_widget = self.game_widgets[self.current_game]
            game_widget.mousePressEvent(event)
        else:
            # Handle tap outside game items - go back
            if not any(label.geometry().contains(event.pos()) for label in self.game_labels):
                self._go_back()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Games view activated")
        self.selected_index = 0
        self.current_game = None
        self.stack.setCurrentWidget(self.list_view)
        self._update_display()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Games view deactivated")
        
        # Deactivate any active game
        if self.current_game:
            game_widget = self.game_widgets[self.current_game]
            if hasattr(game_widget, 'on_deactivate'):
                game_widget.on_deactivate()
            self.current_game = None
