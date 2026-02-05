"""
Message Overlay Widget - Retro Hardware Style
Full-screen message overlay that blocks all interaction.
"""

import logging
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QSound

logger = logging.getLogger(__name__)


class MessageOverlay(QWidget):
    """
    Full-screen message overlay.
    Blocks all interaction until dismissed.
    Auto-dismisses after 3 minutes.
    """
    
    dismissed = pyqtSignal()
    
    AUTO_DISMISS_MS = 3 * 60 * 1000  # 3 minutes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = ""
        self.body = ""
        self.auto_dismiss_timer = None
        
        self._init_ui()
        self.hide()  # Hidden by default
    
    def _init_ui(self):
        """Initialize UI components."""
        # Full screen, pure black background
        self.setStyleSheet("background-color: #000000;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("MESSAGE")
        header.setFont(QFont("Courier New", 28, QFont.Bold))
        header.setStyleSheet("color: #E0E0E0; background: transparent;")
        header.setAlignment(Qt.AlignLeft)
        layout.addWidget(header)
        
        # Separator line
        separator = QLabel("─" * 40)
        separator.setFont(QFont("Courier New", 16))
        separator.setStyleSheet("color: #606060; background: transparent;")
        layout.addWidget(separator)
        
        layout.addSpacing(40)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Courier New", 24, QFont.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title_label)
        
        layout.addSpacing(20)
        
        # Body
        self.body_label = QLabel()
        self.body_label.setFont(QFont("Courier New", 18))
        self.body_label.setStyleSheet("color: #C0C0C0; background: transparent;")
        self.body_label.setWordWrap(True)
        self.body_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.body_label)
        
        layout.addStretch()
        
        # Dismiss hint
        self.hint_label = QLabel("[A] DISMISS")
        self.hint_label.setFont(QFont("Courier New", 16))
        self.hint_label.setStyleSheet("color: #808080; background: transparent;")
        self.hint_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.hint_label)
    
    def show_message(self, title: str, body: str):
        """Show a message overlay."""
        self.title = title
        self.body = body
        
        self.title_label.setText(title)
        self.body_label.setText(body)
        
        # Play chime sound
        self._play_chime()
        
        # Start auto-dismiss timer
        if self.auto_dismiss_timer:
            self.auto_dismiss_timer.stop()
        self.auto_dismiss_timer = QTimer(self)
        self.auto_dismiss_timer.setSingleShot(True)
        self.auto_dismiss_timer.timeout.connect(self.dismiss)
        self.auto_dismiss_timer.start(self.AUTO_DISMISS_MS)
        
        self.show()
        self.raise_()
        self.setFocus()
        
        logger.info(f"Message overlay shown: {title}")
    
    def _play_chime(self):
        """Play notification chime."""
        try:
            # Try to play a simple notification sound
            # You can replace with an actual sound file path
            pass
        except Exception as e:
            logger.debug(f"Could not play chime: {e}")
    
    def dismiss(self):
        """Dismiss the overlay."""
        if self.auto_dismiss_timer:
            self.auto_dismiss_timer.stop()
            self.auto_dismiss_timer = None
        
        self.hide()
        self.dismissed.emit()
        logger.info("Message overlay dismissed")
    
    def keyPressEvent(self, event):
        """Handle key press - dismiss on A or any key."""
        key = event.key()
        if key in (Qt.Key_A, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Escape):
            self.dismiss()
        else:
            # Consume all other keys to block interaction
            event.accept()
    
    def mousePressEvent(self, event):
        """Handle mouse press - dismiss overlay."""
        self.dismiss()
