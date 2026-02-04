"""
Main Window
Root window containing navigation and view stack.
"""

import logging
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent
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
        
        # Initialize services
        self.photo_service = PhotoService(app_state)
        self.music_service = MusicService(app_state)
        
        # Setup UI
        self._init_ui()
        
        # Install event filter for tracking interactions
        self.installEventFilter(self)
        
        # Idle timer - check every 5 seconds
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._check_idle)
        self.idle_timer.start(5000)
        
        # Start services
        self.photo_service.start()
        
        logger.info("MainWindow initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Window properties
        self.setWindowTitle("Smart Frame")
        
        if self.fullscreen:
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)  # Hide cursor in kiosk mode
        else:
            width = self.app_state.get_setting('display_width', 1024)
            height = self.app_state.get_setting('display_height', 600)
            self.resize(width, height)
        
        # Remove window frame
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layouidle_view = IdleView(self.app_state, lambda: self._navigate(AppState.VIEW_HOME))
        self.home_view = HomeView(
            self.app_state, 
            self._navigate,
            show_messages_callback=lambda: self._navigate(AppState.VIEW_MESSAGES),
            show_games_callback=lambda: self._navigate(AppState.VIEW_GAMES)
        )
        self.photo_view = PhotoView(self.app_state, self.photo_service, self._navigate)
        self.music_view = MusicView(self.app_state, self.music_service, self._navigate)
        self.settings_view = SettingsView(self.app_state, self._navigate)
        self.messages_view = MessagesView(self.app_state, self._navigate)
        self.games_view = GamesView(self.app_state, self._navigate)
        
        # Add views to stack
        self.views = {
            AppState.VIEW_IDLE: self.idle_view,
            AppState.VIEW_HOME: self.home_view,
            AppState.VIEW_PHOTOS: self.photo_view,
            AppState.VIEW_MUSIC: self.music_view,
            AppState.VIEW_SETTINGS: self.settings_view,
            AppState.VIEW_MESSAGES: self.messages_view,
            AppState.VIEW_GAMES: self.games_view,
        }
        
        for view_name, view_widget in self.views.items():
            self.stack.addWidget(view_widget)
        
        # Show idle view initially
        self._navigate(AppState.VIEW_IDLsic_view,
            AppState.VIEW_SETTINGS: self.settings_view,
        }
        
        for view_name, view_widget in self.views.items():
            self.stack.addWidget(view_widget)
        
        # Show home view
        self._navigate(AppState.VIEW_HOME)
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        from PyQt5.QtWidgets import QShortcut
        
        # Escape or Q to quit (useful for development)
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)
        
        # F11 to toggle fullscreen
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
            self.setCursor(Qt.ArrowCursor)
        else:
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)
    self.app_state.update_interaction()
            
            # Activate/deactivate views as needed
            for name, view in self.views.items():
                if name == view_name:
                    if hasattr(view, 'on_activate'):
                        view.on_activate()
                    self.stack.setCurrentWidget(view)
                else:
                    if hasattr(view, 'on_deactivate'):
                        view.on_deactivate()
    
    def _check_idle(self):
        """Check if we should return to idle view."""
        if self.app_state.should_go_idle():
            logger.info("Idle timeout - returning to idle view")
            self._navigate(AppState.VIEW_IDLE)
    
    def eventFilter(self, obj, event):
        """Filter events to track user interaction."""
        # Track mouse and keyboard events as interaction
        if event.type() in [
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseMove,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.TouchBegin,
            QEvent.TouchEnd
        ]:
            self.app_state.update_interaction()
        
        return super().eventFilter(obj, eventiew_name}")
            self.app_state.set_current_view(view_name)
            
            # Activate/deactivate views as needed
            for name, view in self.views.items():
                if name == view_name:
                    if hasattr(view, 'on_activate'):
                        view.on_activate()
                    self.stack.setCurrentWidget(view)
                else:
                    if hasattr(view, 'on_deactivate'):
                        view.on_deactivate()
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Closing main window, cleaning up...")
        
        # Stop services
        self.photo_service.stop()
        self.music_service.stop()
        
        # Cleanup state
        self.app_state.cleanup()
        
        event.accept()
