"""
Tic-Tac-Toe Game - Native PyQt5 Implementation
Classic X-O game with AI opponent. Retro hardware style.
"""

import logging
import random
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont

logger = logging.getLogger(__name__)


class TicTacToeWidget(QWidget):
    """
    Tic-Tac-Toe game widget - Retro hardware style.
    
    3x3 grid.
    Player is X, AI is O.
    Click to place mark.
    """
    
    game_over = pyqtSignal(str)  # Emit result: 'win', 'lose', 'draw'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'  # Player is X
        self.is_game_over = False
        self.winner = None
        self.winning_line = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setStyleSheet("background-color: #000000;")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 400)
    
    def reset_game(self):
        """Reset the game."""
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.is_game_over = False
        self.winner = None
        self.winning_line = None
        self.update()
        logger.info("Tic-Tac-Toe game reset")
    
    def _check_winner(self):
        """Check if there's a winner."""
        # Check rows
        for i in range(3):
            if self.board[i][0] and self.board[i][0] == self.board[i][1] == self.board[i][2]:
                self.winning_line = ('row', i)
                return self.board[i][0]
        
        # Check columns
        for j in range(3):
            if self.board[0][j] and self.board[0][j] == self.board[1][j] == self.board[2][j]:
                self.winning_line = ('col', j)
                return self.board[0][j]
        
        # Check diagonals
        if self.board[0][0] and self.board[0][0] == self.board[1][1] == self.board[2][2]:
            self.winning_line = ('diag', 0)
            return self.board[0][0]
        
        if self.board[0][2] and self.board[0][2] == self.board[1][1] == self.board[2][0]:
            self.winning_line = ('diag', 1)
            return self.board[0][2]
        
        return None
    
    def _is_board_full(self):
        """Check if board is full."""
        for row in self.board:
            if '' in row:
                return False
        return True
    
    def _make_move(self, row, col):
        """Make a move on the board."""
        if self.is_game_over or self.board[row][col]:
            return False
        
        self.board[row][col] = self.current_player
        self.update()
        
        # Check for winner
        winner = self._check_winner()
        if winner:
            self.is_game_over = True
            self.winner = winner
            logger.info(f"Game over - Winner: {winner}")
            result = 'win' if winner == 'X' else 'lose'
            QTimer.singleShot(500, lambda: self.game_over.emit(result))
            return True
        
        # Check for draw
        if self._is_board_full():
            self.is_game_over = True
            self.winner = 'Draw'
            logger.info("Game over - Draw")
            QTimer.singleShot(500, lambda: self.game_over.emit('draw'))
            return True
        
        # Switch player
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.update()
        
        # AI move (if it's O's turn)
        if self.current_player == 'O':
            QTimer.singleShot(500, self._ai_move)
        
        return True
    
    def _ai_move(self):
        """AI makes a move (simple strategy)."""
        if self.is_game_over:
            return
        
        # Try to win
        move = self._find_winning_move('O')
        if move:
            self._make_move(move[0], move[1])
            return
        
        # Block player from winning
        move = self._find_winning_move('X')
        if move:
            self._make_move(move[0], move[1])
            return
        
        # Take center if available
        if not self.board[1][1]:
            self._make_move(1, 1)
            return
        
        # Take a corner
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        random.shuffle(corners)
        for r, c in corners:
            if not self.board[r][c]:
                self._make_move(r, c)
                return
        
        # Take any available space
        for i in range(3):
            for j in range(3):
                if not self.board[i][j]:
                    self._make_move(i, j)
                    return
    
    def _find_winning_move(self, player):
        """Find a winning move for the given player."""
        for i in range(3):
            for j in range(3):
                if not self.board[i][j]:
                    # Try this move
                    self.board[i][j] = player
                    winner = self._check_winner()
                    self.board[i][j] = ''  # Undo
                    self.winning_line = None
                    if winner == player:
                        return (i, j)
        return None
    
    def paintEvent(self, event):
        """Paint the game."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Calculate board size
        board_size = min(w, h) - 100
        cell_size = board_size // 3
        offset_x = (w - board_size) // 2
        offset_y = (h - board_size) // 2 + 20
        
        # Draw grid
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        for i in range(1, 3):
            # Vertical lines
            x = offset_x + i * cell_size
            painter.drawLine(x, offset_y, x, offset_y + board_size)
            # Horizontal lines
            y = offset_y + i * cell_size
            painter.drawLine(offset_x, y, offset_x + board_size, y)
        
        # Draw X's and O's
        for i in range(3):
            for j in range(3):
                if self.board[i][j]:
                    self._draw_mark(painter, i, j, self.board[i][j], 
                                  offset_x, offset_y, cell_size)
        
        # Draw winning line
        if self.winning_line:
            self._draw_winning_line(painter, offset_x, offset_y, cell_size, board_size)
        
        # Draw status
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Courier New", 18, QFont.Bold)
        painter.setFont(font)
        
        if self.is_game_over:
            if self.winner == 'Draw':
                status = "DRAW!"
                color = QColor(200, 200, 100)
            elif self.winner == 'X':
                status = "YOU WIN!"
                color = QColor(100, 255, 100)
            else:
                status = "YOU LOSE!"
                color = QColor(255, 100, 100)
            
            painter.setPen(color)
            font = QFont("Courier New", 24, QFont.Bold)
            painter.setFont(font)
            painter.drawText(0, offset_y - 50, w, 40, Qt.AlignCenter, status)
            
            painter.setPen(QColor(150, 150, 150))
            font = QFont("Courier New", 14)
            painter.setFont(font)
            painter.drawText(0, h - 40, w, 30, Qt.AlignCenter, "Tap to play again")
        else:
            status = "Your turn (X)" if self.current_player == 'X' else "AI thinking (O)..."
            painter.drawText(0, offset_y - 50, w, 40, Qt.AlignCenter, status)
    
    def _draw_mark(self, painter, row, col, mark, offset_x, offset_y, cell_size):
        """Draw X or O."""
        x = offset_x + col * cell_size
        y = offset_y + row * cell_size
        margin = cell_size // 5
        
        if mark == 'X':
            # Draw X
            painter.setPen(QPen(QColor(100, 200, 255), 5, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(x + margin, y + margin, 
                           x + cell_size - margin, y + cell_size - margin)
            painter.drawLine(x + cell_size - margin, y + margin,
                           x + margin, y + cell_size - margin)
        else:
            # Draw O
            painter.setPen(QPen(QColor(255, 150, 100), 5))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(x + margin, y + margin,
                              cell_size - 2 * margin, cell_size - 2 * margin)
    
    def _draw_winning_line(self, painter, offset_x, offset_y, cell_size, board_size):
        """Draw line through winning marks."""
        painter.setPen(QPen(QColor(100, 255, 100), 5))
        
        line_type, index = self.winning_line
        
        if line_type == 'row':
            y = offset_y + index * cell_size + cell_size // 2
            painter.drawLine(offset_x, y, offset_x + board_size, y)
        elif line_type == 'col':
            x = offset_x + index * cell_size + cell_size // 2
            painter.drawLine(x, offset_y, x, offset_y + board_size)
        elif line_type == 'diag':
            if index == 0:
                painter.drawLine(offset_x, offset_y, 
                               offset_x + board_size, offset_y + board_size)
            else:
                painter.drawLine(offset_x + board_size, offset_y,
                               offset_x, offset_y + board_size)
    
    def mousePressEvent(self, event):
        """Handle mouse/touch input."""
        if self.is_game_over:
            # Tap to restart
            self.reset_game()
            return
        
        if self.current_player != 'X':
            # Not player's turn
            return
        
        w, h = self.width(), self.height()
        board_size = min(w, h) - 100
        cell_size = board_size // 3
        offset_x = (w - board_size) // 2
        offset_y = (h - board_size) // 2 + 20
        
        # Calculate which cell was clicked
        x = event.pos().x() - offset_x
        y = event.pos().y() - offset_y
        
        if x < 0 or y < 0 or x >= board_size or y >= board_size:
            return
        
        col = x // cell_size
        row = y // cell_size
        
        self._make_move(row, col)
    
    def on_activate(self):
        """Called when game becomes active."""
        self.reset_game()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when game becomes inactive."""
        pass
