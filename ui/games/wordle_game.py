"""
Wordle Game - Native PyQt5 Implementation
Daily word guessing game. Retro hardware style.
"""

import logging
import random
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QKeyEvent

logger = logging.getLogger(__name__)


class WordleWidget(QWidget):
    """
    Wordle game widget - Retro hardware style.
    
    Guess a 5-letter word in 6 attempts.
    Green = correct letter, correct position.
    Yellow = correct letter, wrong position.
    Gray = letter not in word.
    """
    
    game_over = pyqtSignal(bool, int)  # Emit (won, attempts_used)
    
    # Word list (common 5-letter words)
    WORD_LIST = [
        'APPLE', 'BEACH', 'BRAIN', 'BREAD', 'BRUSH', 'CHAIR', 'CHESS',
        'CLOUD', 'CORAL', 'DREAM', 'EARTH', 'FLAME', 'FLASH', 'FRUIT',
        'GRAPE', 'GRASS', 'GREEN', 'HAPPY', 'HEART', 'HONEY', 'HOUSE',
        'JUICE', 'LEMON', 'LIGHT', 'LUNAR', 'MAPLE', 'MELON', 'MONEY',
        'NIGHT', 'OCEAN', 'OLIVE', 'PAINT', 'PEACE', 'PEACH', 'PIANO',
        'PLANT', 'POWER', 'PRIDE', 'QUIET', 'RAINY', 'RIVER', 'ROYAL',
        'SHORE', 'SLEEP', 'SMILE', 'SNOWY', 'SOLAR', 'SPACE', 'SPICE',
        'STAND', 'STEEL', 'STONE', 'STORM', 'STUDY', 'SUGAR', 'SUNNY',
        'SWEET', 'TABLE', 'TIGER', 'TOAST', 'TODAY', 'TOWER', 'TRAIN',
        'TRUST', 'TRUTH', 'TULIP', 'URBAN', 'VALUE', 'VITAL', 'VIVID',
        'WATCH', 'WATER', 'WHEAT', 'WHEEL', 'WHITE', 'WORLD', 'WORTH'
    ]
    
    # Keyboard layout
    KEYBOARD_ROWS = [
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
    ]
    
    MAX_ATTEMPTS = 6
    WORD_LENGTH = 5
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.target_word = ''
        self.current_guess = ''
        self.attempts = []  # List of guessed words
        self.is_game_over = False
        self.is_won = False
        self.letter_states = {}  # Track letter colors for keyboard
        
        self._init_ui()
        self.reset_game()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setStyleSheet("background-color: #000000;")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 600)
    
    def reset_game(self):
        """Reset the game with a new word."""
        # Get daily word (deterministic based on date)
        today = datetime.now().date()
        seed = int(today.strftime("%Y%m%d"))
        random.seed(seed)
        self.target_word = random.choice(self.WORD_LIST)
        random.seed()  # Reset seed
        
        self.current_guess = ''
        self.attempts = []
        self.is_game_over = False
        self.is_won = False
        self.letter_states = {}
        
        logger.info(f"Wordle game reset - Target word: {self.target_word}")
        self.update()
    
    def _submit_guess(self):
        """Submit the current guess."""
        if len(self.current_guess) != self.WORD_LENGTH:
            return
        
        if self.current_guess not in self.WORD_LIST:
            # Invalid word - could add visual feedback
            logger.info(f"Invalid word: {self.current_guess}")
            return
        
        # Add to attempts
        self.attempts.append(self.current_guess)
        
        # Update letter states for keyboard
        self._update_letter_states(self.current_guess)
        
        # Check if won
        if self.current_guess == self.target_word:
            self.is_game_over = True
            self.is_won = True
            logger.info(f"Wordle won in {len(self.attempts)} attempts")
            QTimer.singleShot(500, lambda: self.game_over.emit(True, len(self.attempts)))
        # Check if out of attempts
        elif len(self.attempts) >= self.MAX_ATTEMPTS:
            self.is_game_over = True
            self.is_won = False
            logger.info(f"Wordle lost - Word was: {self.target_word}")
            QTimer.singleShot(500, lambda: self.game_over.emit(False, len(self.attempts)))
        
        self.current_guess = ''
        self.update()
    
    def _update_letter_states(self, word):
        """Update letter states based on guess."""
        for i, letter in enumerate(word):
            if letter == self.target_word[i]:
                self.letter_states[letter] = 'correct'  # Green
            elif letter in self.target_word:
                if self.letter_states.get(letter) != 'correct':
                    self.letter_states[letter] = 'present'  # Yellow
            else:
                if letter not in self.letter_states:
                    self.letter_states[letter] = 'absent'  # Gray
    
    def _get_letter_color(self, word, index):
        """Get color for a letter in a guessed word."""
        letter = word[index]
        
        # Correct position
        if letter == self.target_word[index]:
            return QColor(100, 200, 100)  # Green
        
        # Letter in word but wrong position
        if letter in self.target_word:
            return QColor(200, 200, 100)  # Yellow
        
        # Letter not in word
        return QColor(80, 80, 80)  # Gray
    
    def paintEvent(self, event):
        """Paint the game."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw title
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Courier New", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 30, w, 30, Qt.AlignCenter, "WORDLE")
        
        # Draw grid
        self._draw_grid(painter)
        
        # Draw keyboard
        self._draw_keyboard(painter)
        
        # Draw game over message
        if self.is_game_over:
            self._draw_game_over(painter)
    
    def _draw_grid(self, painter):
        """Draw the guess grid."""
        w = self.width()
        
        cell_size = 50
        spacing = 5
        grid_width = self.WORD_LENGTH * (cell_size + spacing) - spacing
        start_x = (w - grid_width) // 2
        start_y = 80
        
        # Draw previous attempts
        for row_idx, word in enumerate(self.attempts):
            y = start_y + row_idx * (cell_size + spacing)
            for col_idx, letter in enumerate(word):
                x = start_x + col_idx * (cell_size + spacing)
                color = self._get_letter_color(word, col_idx)
                self._draw_cell(painter, x, y, cell_size, letter, color)
        
        # Draw current guess row
        if not self.is_game_over and len(self.attempts) < self.MAX_ATTEMPTS:
            row_idx = len(self.attempts)
            y = start_y + row_idx * (cell_size + spacing)
            for col_idx in range(self.WORD_LENGTH):
                x = start_x + col_idx * (cell_size + spacing)
                letter = self.current_guess[col_idx] if col_idx < len(self.current_guess) else ''
                self._draw_cell(painter, x, y, cell_size, letter, QColor(40, 40, 40))
        
        # Draw empty rows
        for row_idx in range(len(self.attempts) + (0 if self.is_game_over else 1), self.MAX_ATTEMPTS):
            y = start_y + row_idx * (cell_size + spacing)
            for col_idx in range(self.WORD_LENGTH):
                x = start_x + col_idx * (cell_size + spacing)
                self._draw_cell(painter, x, y, cell_size, '', QColor(30, 30, 30))
    
    def _draw_cell(self, painter, x, y, size, letter, color):
        """Draw a single cell."""
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(color))
        painter.drawRect(x, y, size, size)
        
        if letter:
            painter.setPen(QColor(240, 240, 240))
            font = QFont("Courier New", 20, QFont.Bold)
            painter.setFont(font)
            painter.drawText(x, y, size, size, Qt.AlignCenter, letter)
    
    def _draw_keyboard(self, painter):
        """Draw the on-screen keyboard."""
        w, h = self.width(), self.height()
        
        key_w = 35
        key_h = 45
        spacing = 4
        
        start_y = h - 180
        
        for row_idx, row in enumerate(self.KEYBOARD_ROWS):
            row_width = len(row) * (key_w + spacing) - spacing
            start_x = (w - row_width) // 2
            y = start_y + row_idx * (key_h + spacing)
            
            for col_idx, letter in enumerate(row):
                x = start_x + col_idx * (key_w + spacing)
                
                # Color based on letter state
                if letter in self.letter_states:
                    state = self.letter_states[letter]
                    if state == 'correct':
                        color = QColor(100, 200, 100)
                    elif state == 'present':
                        color = QColor(200, 200, 100)
                    else:
                        color = QColor(60, 60, 60)
                else:
                    color = QColor(80, 80, 80)
                
                self._draw_key(painter, x, y, key_w, key_h, letter, color)
        
        # Draw ENTER and BACK keys
        enter_y = start_y + 3 * (key_h + spacing)
        back_x = w // 2 - 80
        enter_x = w // 2 + 20
        
        self._draw_key(painter, enter_x, enter_y, 60, key_h, "ENTER", QColor(80, 120, 80))
        self._draw_key(painter, back_x, enter_y, 60, key_h, "⌫", QColor(120, 80, 80))
    
    def _draw_key(self, painter, x, y, w, h, text, color):
        """Draw a keyboard key."""
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(color))
        painter.drawRect(x, y, w, h)
        
        painter.setPen(QColor(240, 240, 240))
        font = QFont("Courier New", 10 if len(text) > 1 else 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(x, y, w, h, Qt.AlignCenter, text)
    
    def _draw_game_over(self, painter):
        """Draw game over message."""
        w, h = self.width(), self.height()
        
        if self.is_won:
            text = "YOU WIN!"
            color = QColor(100, 255, 100)
        else:
            text = f"WORD: {self.target_word}"
            color = QColor(255, 150, 100)
        
        painter.setPen(color)
        font = QFont("Courier New", 20, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 440, w, 30, Qt.AlignCenter, text)
        
        painter.setPen(QColor(150, 150, 150))
        font = QFont("Courier New", 12)
        painter.setFont(font)
        painter.drawText(0, 470, w, 20, Qt.AlignCenter, "Press R to restart")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input."""
        if self.is_game_over:
            if event.key() == Qt.Key_R:
                self.reset_game()
            return
        
        key = event.key()
        
        # Letter input
        if Qt.Key_A <= key <= Qt.Key_Z:
            letter = chr(key)
            if len(self.current_guess) < self.WORD_LENGTH:
                self.current_guess += letter
                self.update()
        
        # Backspace
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            if self.current_guess:
                self.current_guess = self.current_guess[:-1]
                self.update()
        
        # Enter
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self._submit_guess()
        
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse/touch input for on-screen keyboard."""
        if self.is_game_over:
            # Tap to restart
            self.reset_game()
            return
        
        w, h = self.width(), self.height()
        x, y = event.pos().x(), event.pos().y()
        
        key_w = 35
        key_h = 45
        spacing = 4
        start_y = h - 180
        
        # Check keyboard rows
        for row_idx, row in enumerate(self.KEYBOARD_ROWS):
            row_width = len(row) * (key_w + spacing) - spacing
            start_x = (w - row_width) // 2
            row_y = start_y + row_idx * (key_h + spacing)
            
            if row_y <= y <= row_y + key_h:
                for col_idx, letter in enumerate(row):
                    key_x = start_x + col_idx * (key_w + spacing)
                    if key_x <= x <= key_x + key_w:
                        if len(self.current_guess) < self.WORD_LENGTH:
                            self.current_guess += letter
                            self.update()
                        return
        
        # Check ENTER and BACK keys
        enter_y = start_y + 3 * (key_h + spacing)
        back_x = w // 2 - 80
        enter_x = w // 2 + 20
        
        if enter_y <= y <= enter_y + key_h:
            if enter_x <= x <= enter_x + 60:
                self._submit_guess()
            elif back_x <= x <= back_x + 60:
                if self.current_guess:
                    self.current_guess = self.current_guess[:-1]
                    self.update()
    
    def on_activate(self):
        """Called when game becomes active."""
        self.reset_game()
        self.setFocus()
    
    def on_deactivate(self):
        """Called when game becomes inactive."""
        pass
