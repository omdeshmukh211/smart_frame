"""
Games View
Simple game selection and placeholder for future game implementations.
"""

import logging
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout)
from PyQt5.QtGui import QFont

from models.app_state import AppState

logger = logging.getLogger(__name__)


class GameCard(QPushButton):
    """Game selection card."""
    
    def __init__(self, icon, title, description, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 220)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 60px;
            background: transparent;
        """)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #fff;
            font-size: 18px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 12px;
            background: transparent;
        """)
        layout.addWidget(desc_label)
        
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)


class GamesView(QWidget):
    """
    Games selection view.
    Shows available games and allows launching them.
    """
    
    closed = pyqtSignal()
    
    def __init__(self, app_state: AppState, navigate_callback=None):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        
        self._init_ui()
    
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
        title = QLabel("🎮 Games")
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
        
        # Game cards grid
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(50, 50, 50, 50)
        content_layout.setAlignment(Qt.AlignCenter)
        
        grid = QGridLayout()
        grid.setSpacing(25)
        grid.setAlignment(Qt.AlignCenter)
        
        # Snake game
        snake_card = GameCard("🐍", "Snake", "Classic snake game")
        snake_card.clicked.connect(lambda: self._launch_game("snake"))
        grid.addWidget(snake_card, 0, 0)
        
        # Tic-Tac-Toe
        ttt_card = GameCard("❌⭕", "Tic-Tac-Toe", "Play against AI")
        ttt_card.clicked.connect(lambda: self._launch_game("tictactoe"))
        grid.addWidget(ttt_card, 0, 1)
        
        # Wordle
        wordle_card = GameCard("🔤", "Wordle", "Guess the word")
        wordle_card.clicked.connect(lambda: self._launch_game("wordle"))
        grid.addWidget(wordle_card, 1, 0)
        
        # Memory Game
        memory_card = GameCard("🧠", "Memory", "Match the pairs")
        memory_card.clicked.connect(lambda: self._launch_game("memory"))
        grid.addWidget(memory_card, 1, 1)
        
        content_layout.addLayout(grid)
        
        # Coming soon label
        coming_soon = QLabel("More games coming soon!")
        coming_soon.setAlignment(Qt.AlignCenter)
        coming_soon.setStyleSheet("""
            color: rgba(255, 255, 255, 0.4);
            font-size: 16px;
            font-style: italic;
            padding-top: 30px;
            background: transparent;
        """)
        content_layout.addWidget(coming_soon)
        
        layout.addWidget(content_widget)
    
    def _launch_game(self, game_name):
        """Launch a game (placeholder for now)."""
        logger.info(f"Launching game: {game_name}")
        
        # For now, just show a message
        # In a full implementation, this would switch to a game view
        from PyQt5.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"{game_name.title()} Game")
        msg.setText(f"🎮 {game_name.title()} game will be implemented here!\n\nComing soon...")
        msg.setStyleSheet("""
            QMessageBox {
                background: #1a1a2e;
            }
            QLabel {
                color: #fff;
                font-size: 16px;
                padding: 20px;
            }
            QPushButton {
                background: #2196F3;
                color: white;
                padding: 10px 30px;
                border-radius: 5px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        msg.exec_()
    
    def _close(self):
        """Close games view."""
        self.closed.emit()
        if self.navigate:
            self.navigate(AppState.VIEW_HOME)
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Games view activated")
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Games view deactivated")
