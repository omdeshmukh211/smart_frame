"""
Main Window - Retro Hardware Style
Root window containing navigation and view stack.
Fixed resolution display (1024x600).
"""

import logging
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtGui import QKeySequence, QFont, QFontDatabase

from models.app_state import AppState
from ui.views.idle_view import IdleView
from ui.views.home_view import HomeView
from ui.views.menu_view import MenuView
from ui.views.photo_view import PhotoView
from ui.views.music_view import MusicView
from ui.views.settings_view import SettingsView
from ui.views.messages_view import MessagesView
from ui.views.games_view import GamesView
from ui.widgets.message_overlay import MessageOverlay
from services.photo_service import PhotoService
from services.music_service import MusicService
from services.voice_service import VoiceService

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class MainWindow(QMainWindow):
    """
    Main application window - Retro Hardware Style.
    Fixed resolution display device interface.
    
    Screen Architecture:
    [ IDLE ] ← default → tap → [ HOME ] → tap → [ MENU ]
    """

    # Fixed display resolution
    DISPLAY_WIDTH = 1024
    DISPLAY_HEIGHT = 600

    def __init__(self, app_state: AppState, fullscreen=True):
        super().__init__()
        self.app_state = app_state
        self.fullscreen = fullscreen
        self.message_overlay = None

        # Background services
        self.photo_service = PhotoService(app_state)
        self.music_service = MusicService(app_state)
        self.voice_service = None  # Will be initialized after views

        self._init_ui()

        # Track interaction globally
        self.installEventFilter(self)

        # Idle timer
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._check_idle)
        self.idle_timer.start(5000)

        self.photo_service.start()
        logger.info("MainWindow initialized - Retro Hardware UI")

    def _init_ui(self):
        self.setWindowTitle("Smart Frame")

        if self.fullscreen:
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)
        else:
            self.setFixedSize(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)

        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Pure black background
        self.setStyleSheet("background-color: #000000;")

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Views - Retro Hardware Style
        self.idle_view = IdleView(self.app_state, lambda: self._navigate(AppState.VIEW_HOME))
        self.home_view = HomeView(self.app_state, self._navigate)
        self.menu_view = MenuView(self.app_state, self._navigate)
        self.photo_view = PhotoView(self.app_state, self.photo_service, self._navigate)
        self.music_view = MusicView(self.app_state, self.music_service, self._navigate)
        self.settings_view = SettingsView(self.app_state, self._navigate)
        self.messages_view = MessagesView(self.app_state, self._navigate)
        self.games_view = GamesView(self.app_state, self._navigate)

        self.views = {
            AppState.VIEW_IDLE: self.idle_view,
            AppState.VIEW_HOME: self.home_view,
            AppState.VIEW_MENU: self.menu_view,
            AppState.VIEW_PHOTOS: self.photo_view,
            AppState.VIEW_MUSIC: self.music_view,
            AppState.VIEW_SETTINGS: self.settings_view,
            AppState.VIEW_MESSAGES: self.messages_view,
            AppState.VIEW_GAMES: self.games_view,
        }

        for view in self.views.values():
            self.stack.addWidget(view)

        # Message overlay (always on top)
        self.message_overlay = MessageOverlay(central)
        self.message_overlay.dismissed.connect(self._on_overlay_dismissed)

        # Initialize voice service after views are created
        self.voice_service = VoiceService(self.app_state, self._navigate)
        self.voice_service.wake_detected.connect(self._on_wake_detected)
        self.voice_service.transcription_ready.connect(self._on_transcription)
        self.voice_service.command_executed.connect(self._on_command_executed)
        
        # Connect voice service to home view for mic control
        self.home_view.mic_toggled = self._on_mic_toggled

        self._navigate(AppState.VIEW_IDLE)
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        from PyQt5.QtWidgets import QShortcut

        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._handle_back)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.setFixedSize(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
            self.setCursor(Qt.ArrowCursor)
        else:
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)

    def _handle_back(self):
        """Handle back/escape navigation."""
        current = self.app_state.get_current_view()
        if current == AppState.VIEW_MENU:
            self._navigate(AppState.VIEW_HOME)
        elif current == AppState.VIEW_HOME:
            self._navigate(AppState.VIEW_IDLE)
        elif current in (AppState.VIEW_GAMES, AppState.VIEW_MUSIC, 
                        AppState.VIEW_MESSAGES, AppState.VIEW_SETTINGS,
                        AppState.VIEW_PHOTOS):
            self._navigate(AppState.VIEW_MENU)

    def _navigate(self, view_name: str):
        # Don't navigate if overlay is showing
        if self.message_overlay and self.message_overlay.isVisible():
            return
            
        if view_name not in self.views:
            return

        logger.info("Navigating to %s", view_name)
        self.app_state.set_current_view(view_name)
        self.app_state.update_interaction()

        for name, view in self.views.items():
            if name == view_name:
                if hasattr(view, "on_activate"):
                    view.on_activate()
                self.stack.setCurrentWidget(view)
            else:
                if hasattr(view, "on_deactivate"):
                    view.on_deactivate()

    def _check_idle(self):
        # Don't go idle if overlay is showing
        if self.message_overlay and self.message_overlay.isVisible():
            return
        if self.app_state.should_go_idle():
            self._navigate(AppState.VIEW_IDLE)

    @pyqtSlot(str, str)
    def show_system_message(self, title: str, body: str):
        """Show a system message overlay."""
        if self.message_overlay:
            self.message_overlay.show_message(title, body)
    
    def _on_overlay_dismissed(self):
        """Called when message overlay is dismissed."""
        logger.info("Message overlay dismissed, resuming normal operation")
    
    def _on_wake_detected(self):
        """Called when wake phrase is detected."""
        logger.info("Wake phrase detected")
        # Update home view to show mic is active
        if hasattr(self.home_view, 'set_mic_active'):
            self.home_view.set_mic_active(True)
    
    def _on_transcription(self, text: str):
        """Called when speech is transcribed."""
        logger.info(f"Transcription: {text}")
        # Show transcription on home view
        if hasattr(self.home_view, 'show_transcription'):
            self.home_view.show_transcription(text)
    
    def _on_command_executed(self, command: str, success: bool):
        """Called when a command is executed."""
        logger.info(f"Command executed: {command} (success={success})")
        # Clear transcription after command
        if hasattr(self.home_view, 'clear_transcription'):
            QTimer.singleShot(2000, self.home_view.clear_transcription)
    
    def _on_mic_toggled(self, enabled: bool):
        """Called when mic is toggled from home view."""
        logger.info(f"Mic toggled: {enabled}")
        if enabled:
            self.voice_service.start_listening()
        else:
            self.voice_service.stop_listening()

    def eventFilter(self, obj, event):
        # If overlay is visible, capture all input
        if self.message_overlay and self.message_overlay.isVisible():
            if event.type() in (
                QEvent.MouseButtonPress,
                QEvent.KeyPress,
                QEvent.TouchBegin,
            ):
                # Let overlay handle it
                return False
        
        if event.type() in (
            QEvent.MouseButtonPress,
            QEvent.MouseMove,
            QEvent.KeyPress,
            QEvent.TouchBegin,
        ):
            self.app_state.update_interaction()
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        logger.info("Shutting down Smart Frame")

        try:
            self.photo_service.stop()
            self.music_service.stop()
            self.app_state.cleanup()
        except Exception:
            logger.exception("Cleanup failed")

        event.accept()
