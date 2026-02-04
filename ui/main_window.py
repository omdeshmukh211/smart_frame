"""
Main Window
Root window containing navigation and view stack.
"""

import logging
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtGui import QKeySequence

from models.app_state import AppState
from ui.views.home_view import HomeView
from ui.views.photo_view import PhotoView
from ui.views.music_view import MusicView
from ui.views.settings_view import SettingsView
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create stacked widget for views
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Create views
        self.home_view = HomeView(self.app_state, self._navigate)
        self.photo_view = PhotoView(self.app_state, self.photo_service, self._navigate)
        self.music_view = MusicView(self.app_state, self.music_service, self._navigate)
        self.settings_view = SettingsView(self.app_state, self._navigate)
        
        # Add views to stack
        self.views = {
            AppState.VIEW_HOME: self.home_view,
            AppState.VIEW_PHOTOS: self.photo_view,
            AppState.VIEW_MUSIC: self.music_view,
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
    
    def _navigate(self, view_name: str):
        """
        Navigate to a view.
        
        Args:
            view_name: Name of view to navigate to
        """
        if view_name in self.views:
            logger.info(f"Navigating to: {view_name}")
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
