"""
Snake Game - Native PyQt5 Implementation
Classic snake game with retro hardware style.
"""

import logging
import random
from enum import Enum
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QKeyEvent

logger = logging.getLogger(__name__)


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class SnakeGameWidget(QWidget):
    """
    Snake game widget - Retro hardware style.
    
    Grid-based snake movement.
    Food collection grows the snake.
    Game over on collision with walls or self.
    """
    
    game_over = pyqtSignal(int)  # Emit score when game ends
    
    # Grid size
    GRID_SIZE = 20  # 20x20 grid
    GAME_SPEED = 150  # ms per move (adjustable)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.snake = []  # List of (x, y) positions
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food_pos = (0, 0)
        self.score = 0
        self.is_running = False
        self.is_game_over = False
        self.replay_button_rect = QRect()  # For replay button
        
        self._init_ui()
        self._init_timer()
        self.reset_game()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setStyleSheet("background-color: #000000;")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 400)
    
    def _init_timer(self):
        """Initialize game timer."""
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self._game_tick)
    
    def reset_game(self):
        """Reset the game to initial state."""
        # Start snake in the middle
        center = self.GRID_SIZE // 2
        self.snake = [
            (center, center),
            (center - 1, center),
            (center - 2, center)
        ]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.is_game_over = False
        self._spawn_food()
        self.update()
    
    def start_game(self):
        """Start the game."""
        if not self.is_running:
            self.is_running = True
            self.game_timer.start(self.GAME_SPEED)
            logger.info("Snake game started")
    
    def pause_game(self):
        """Pause the game."""
        if self.is_running:
            self.is_running = False
            self.game_timer.stop()
            logger.info("Snake game paused")
    
    def _spawn_food(self):
        """Spawn food at a random position not occupied by snake."""
        while True:
            x = random.randint(0, self.GRID_SIZE - 1)
            y = random.randint(0, self.GRID_SIZE - 1)
            if (x, y) not in self.snake:
                self.food_pos = (x, y)
                break
    
    def _game_tick(self):
        """Game loop tick - move snake."""
        if self.is_game_over:
            return
        
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
        # Check collision with walls
        if (new_head[0] < 0 or new_head[0] >= self.GRID_SIZE or
            new_head[1] < 0 or new_head[1] >= self.GRID_SIZE):
            self._end_game()
            return
        
        # Check collision with self
        if new_head in self.snake:
            self._end_game()
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check if food eaten
        if new_head == self.food_pos:
            self.score += 10
            self._spawn_food()
            # Snake grows (don't remove tail)
        else:
            # Remove tail (snake moves forward)
            self.snake.pop()
        
        self.update()
    
    def _end_game(self):
        """End the game."""
        self.is_game_over = True
        self.is_running = False
        self.game_timer.stop()
        logger.info(f"Snake game over - Score: {self.score}")
        self.game_over.emit(self.score)
        self.update()
    
    def paintEvent(self, event):
        """Paint the game."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw EXIT button at top-right
        painter.setPen(QColor(255, 100, 100))
        painter.setBrush(QBrush(QColor(255, 100, 100, 50)))
        exit_rect = QRect(w - 80, 10, 70, 40)
        painter.drawRoundedRect(exit_rect, 5, 5)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(exit_rect, Qt.AlignCenter, "EXIT")
        
        # Calculate cell size
        grid_size = min(w, h) - 40  # Leave margin
        cell_size = grid_size // self.GRID_SIZE
        offset_x = (w - cell_size * self.GRID_SIZE) // 2
        offset_y = (h - cell_size * self.GRID_SIZE) // 2
        
        # Draw grid
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        for i in range(self.GRID_SIZE + 1):
            # Vertical lines
            x = offset_x + i * cell_size
            painter.drawLine(x, offset_y, x, offset_y + grid_size)
            # Horizontal lines
            y = offset_y + i * cell_size
            painter.drawLine(offset_x, y, offset_x + grid_size, y)
        
        # Draw food
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 100, 100)))  # Red
        fx, fy = self.food_pos
        painter.drawRect(
            offset_x + fx * cell_size + 2,
            offset_y + fy * cell_size + 2,
            cell_size - 4,
            cell_size - 4
        )
        
        # Draw snake
        painter.setBrush(QBrush(QColor(100, 255, 100)))  # Green
        for i, (sx, sy) in enumerate(self.snake):
            # Head slightly different color
            if i == 0:
                painter.setBrush(QBrush(QColor(150, 255, 150)))
            else:
                painter.setBrush(QBrush(QColor(100, 255, 100)))
            
            painter.drawRect(
                offset_x + sx * cell_size + 2,
                offset_y + sy * cell_size + 2,
                cell_size - 4,
                cell_size - 4
            )
        
        # Draw score
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Courier New", 20, QFont.Bold)
        painter.setFont(font)
        painter.drawText(10, 30, f"SCORE: {self.score}")
        
        # Draw game over
        if self.is_game_over:
            # Draw semi-transparent overlay
            overlay = QColor(0, 0, 0, 180)
            painter.fillRect(self.rect(), overlay)
            
            painter.setPen(QColor(255, 100, 100))
            font = QFont("Courier New", 32, QFont.Bold)
            painter.setFont(font)
            painter.drawText(0, 0, w, h - 100, Qt.AlignCenter, "GAME OVER")
            
            painter.setPen(QColor(200, 200, 200))
            font = QFont("Courier New", 18)
            painter.setFont(font)
            painter.drawText(0, h // 2 + 20, w, 30, Qt.AlignCenter, f"Final Score: {self.score}")
            
            # Draw replay button
            button_width, button_height = 120, 40
            button_x = (w - button_width) // 2
            button_y = h // 2 + 60
            self.replay_button_rect = QRect(button_x, button_y, button_width, button_height)
            
            # Draw button background
            painter.setBrush(QColor(100, 200, 100))
            painter.setPen(QColor(80, 160, 80))
            painter.drawRoundedRect(self.replay_button_rect, 8, 8)
            
            # Draw button text
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Courier New", 14, QFont.Bold)
            painter.setFont(font)
            painter.drawText(self.replay_button_rect, Qt.AlignCenter, "REPLAY")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input."""
        key = event.key()
        
        # Direction controls
        if key == Qt.Key_Up and self.direction != Direction.DOWN:
            self.next_direction = Direction.UP
        elif key == Qt.Key_Down and self.direction != Direction.UP:
            self.next_direction = Direction.DOWN
        elif key == Qt.Key_Left and self.direction != Direction.RIGHT:
            self.next_direction = Direction.LEFT
        elif key == Qt.Key_Right and self.direction != Direction.LEFT:
            self.next_direction = Direction.RIGHT
        
        # Game controls
        elif key == Qt.Key_Space:
            if self.is_game_over:
                self.reset_game()
                self.start_game()
            elif self.is_running:
                self.pause_game()
            else:
                self.start_game()
        elif key == Qt.Key_R:
            self.reset_game()
            self.start_game()
        
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle touch/mouse for direction control."""
        if self.is_game_over:
            # Check if replay button was clicked
            if hasattr(self, 'replay_button_rect') and self.replay_button_rect.contains(event.pos()):
                self.reset_game()
                self.start_game()
            return
        
        # Divide screen into 4 zones for direction control
        w, h = self.width(), self.height()
        x, y = event.pos().x(), event.pos().y()
        
        # Calculate which zone was tapped
        center_x = w // 2
        center_y = h // 2
        
        # Top zone
        if y < center_y - 50 and self.direction != Direction.DOWN:
            self.next_direction = Direction.UP
        # Bottom zone
        elif y > center_y + 50 and self.direction != Direction.UP:
            self.next_direction = Direction.DOWN
        # Left zone
        elif x < center_x - 50 and self.direction != Direction.RIGHT:
            self.next_direction = Direction.LEFT
        # Right zone
        elif x > center_x + 50 and self.direction != Direction.LEFT:
            self.next_direction = Direction.RIGHT
        # Center zone - pause/resume
        else:
            if self.is_running:
                self.pause_game()
            else:
                self.start_game()
    
    def on_activate(self):
        """Called when game becomes active."""
        self.reset_game()
        self.start_game()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when game becomes inactive."""
        self.pause_game()
