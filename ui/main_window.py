"""
Main Window
Root window containing navigation and view stack.
"""

import logging
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtGui import QKeySequence

from models.app_state import AppState
from ui.views.idle_view import IdleView
from ui.views.home_view import HomeView
from ui.views.photo_view import PhotoView
from ui.views.music_view import MusicView
from ui.views.settings_view import SettingsView
from ui.views.messages_view import MessagesView
from ui.views.games_view import GamesView
from services.photo_service import PhotoService
from services.music_service import MusicService

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    Manages view navigation and background services.
    """

    def __init__(self, app_state: AppState, fullscreen=True):
        super().__init__()
        self.app_state = app_state
        self.fullscreen = fullscreen

        # Background services
        self.photo_service = PhotoService(app_state)
        self.music_service = MusicService(app_state)

        self._init_ui()

        # Track interaction globally
        self.installEventFilter(self)

        # Idle timer
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._check_idle)
        self.idle_timer.start(5000)

        self.photo_service.start()
        logger.info("MainWindow initialized")

    def _init_ui(self):
        self.setWindowTitle("Smart Frame")

        if self.fullscreen:
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)
        else:
            self.resize(
                self.app_state.get_setting("display_width", 1024),
                self.app_state.get_setting("display_height", 600),
            )

        self.setWindowFlags(Qt.FramelessWindowHint)

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Views
        self.idle_view = IdleView(self.app_state, lambda: self._navigate(AppState.VIEW_HOME))
        self.home_view = HomeView(
            self.app_state,
            self._navigate,
            show_messages_callback=lambda: self._navigate(AppState.VIEW_MESSAGES),
            show_games_callback=lambda: self._navigate(AppState.VIEW_GAMES),
        )
        self.photo_view = PhotoView(self.app_state, self.photo_service, self._navigate)
        self.music_view = MusicView(self.app_state, self.music_service, self._navigate)
        self.settings_view = SettingsView(self.app_state, self._navigate)
        self.messages_view = MessagesView(self.app_state, self._navigate)
        self.games_view = GamesView(self.app_state, self._navigate)

        self.views = {
            AppState.VIEW_IDLE: self.idle_view,
            AppState.VIEW_HOME: self.home_view,
            AppState.VIEW_PHOTOS: self.photo_view,
            AppState.VIEW_MUSIC: self.music_view,
            AppState.VIEW_SETTINGS: self.settings_view,
            AppState.VIEW_MESSAGES: self.messages_view,
            AppState.VIEW_GAMES: self.games_view,
        }

        for view in self.views.values():
            self.stack.addWidget(view)

        self._navigate(AppState.VIEW_IDLE)
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        from PyQt5.QtWidgets import QShortcut

        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.setCursor(Qt.ArrowCursor)
        else:
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)

    def _navigate(self, view_name: str):
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
        if self.app_state.should_go_idle():
            self._navigate(AppState.VIEW_IDLE)

    def eventFilter(self, obj, event):
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
