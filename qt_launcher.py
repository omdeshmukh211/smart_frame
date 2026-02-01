#!/usr/bin/env python3
"""
Smart Frame - PyQt5 Launcher
============================
This script replaces Chromium kiosk mode with a lightweight PyQt5/QtWebEngine window.
It starts the Flask app in a background thread and embeds it in a fullscreen browser widget.

Features:
- Starts Flask server automatically in background
- Creates fullscreen QtWebEngine window (no window decorations)
- Loads the Flask UI from localhost:5000
- Handles graceful shutdown on exit
- Can launch external Chromium for YouTube Music (heavier tasks)

Usage:
    python3 qt_launcher.py [--debug] [--windowed]

Options:
    --debug      Enable debug logging
    --windowed   Run in windowed mode instead of fullscreen (for testing)

Author: Smart Frame Project
"""

import sys
import os
import signal
import logging
import argparse
import subprocess
from threading import Thread
from time import sleep

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# ============================================================================
# Environment Setup (MUST be before PyQt5 imports)
# ============================================================================

# Force software rendering - critical for Raspberry Pi without GPU acceleration
os.environ['QT_QPA_PLATFORM'] = 'xcb'  # X11 backend
os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'  # Required for running as root/service
os.environ['QT_WEBENGINE_DISABLE_GPU'] = '1'  # Disable GPU acceleration
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'  # Force software OpenGL

# Fix for "Illegal instruction" on Raspberry Pi ARM
# Disable AVX/SSE instructions that may not be supported
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = (
    '--disable-gpu '
    '--disable-gpu-compositing '
    '--disable-software-rasterizer '
    '--disable-dev-shm-usage '  # Use /tmp instead of /dev/shm (saves memory)
    '--no-sandbox '
    '--disable-seccomp-filter-sandbox '
    '--disable-extensions '
    '--disable-background-networking '
    '--disable-sync '
    '--disable-translate '
    '--disable-features=TranslateUI,VizDisplayCompositor '
    '--disable-backing-store-limit '
    '--in-process-gpu '
    '--disable-logging '
)

# Disable GPU features that cause illegal instruction on ARM
os.environ['QT_OPENGL'] = 'software'
os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'

# Now import PyQt5
from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel

# ============================================================================
# Configuration
# ============================================================================

FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000
FLASK_URL = f'http://{FLASK_HOST}:{FLASK_PORT}'
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 600

# Logging setup
def setup_logging(debug=False):
    """Configure logging with appropriate level."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(PROJECT_ROOT, 'data', 'qt_launcher.log'))
        ]
    )
    return logging.getLogger('qt_launcher')


# ============================================================================
# Flask Server Thread
# ============================================================================

class FlaskThread(Thread):
    """
    Runs the Flask application in a background thread.
    This allows the Qt main loop to run on the main thread (required by Qt).
    """
    
    def __init__(self, logger):
        super().__init__(daemon=True)  # Daemon thread exits when main thread exits
        self.logger = logger
        self._server = None
        
    def run(self):
        """Start the Flask development server."""
        try:
            self.logger.info("Starting Flask server...")
            
            # Import Flask app here to avoid circular imports
            from app import app
            
            # Disable Flask's reloader (we don't need it in production)
            # and set threaded=True for handling multiple requests
            app.run(
                host=FLASK_HOST,
                port=FLASK_PORT,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Flask server error: {e}")
            raise


# ============================================================================
# JavaScript Bridge for External Browser Launch
# ============================================================================

class ChromiumBridge(QObject):
    """
    Bridge class exposed to JavaScript via QWebChannel.
    Allows the web UI to request launching external Chromium for YouTube Music.
    """
    
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self._chromium_process = None
    
    def launch_youtube_music(self, search_query=""):
        """
        Launch external Chromium browser with YouTube Music.
        Called from JavaScript: window.chromiumBridge.launch_youtube_music("artist name")
        
        Args:
            search_query: Optional artist/song to search for
        """
        self.logger.info(f"Launching YouTube Music with query: {search_query}")
        
        try:
            # Use the existing start_music.sh script
            script_path = os.path.join(PROJECT_ROOT, 'scripts', 'start_music.sh')
            
            if search_query:
                cmd = ['/bin/bash', script_path, search_query]
            else:
                cmd = ['/bin/bash', script_path]
            
            self._chromium_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch Chromium: {e}")
            return False
    
    def stop_youtube_music(self):
        """
        Stop external Chromium browser.
        Called from JavaScript: window.chromiumBridge.stop_youtube_music()
        """
        self.logger.info("Stopping YouTube Music")
        
        try:
            script_path = os.path.join(PROJECT_ROOT, 'scripts', 'stop_music.sh')
            subprocess.run(['/bin/bash', script_path], timeout=10)
            self._chromium_process = None
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop Chromium: {e}")
            return False


# ============================================================================
# Custom WebEngine Page (for handling console messages and errors)
# ============================================================================

class SmartFramePage(QWebEnginePage):
    """Custom WebEngine page with JavaScript console logging."""
    
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
    
    def javaScriptConsoleMessage(self, level, message, line, source):
        """Log JavaScript console messages."""
        level_map = {0: 'INFO', 1: 'WARNING', 2: 'ERROR'}
        level_str = level_map.get(level, 'DEBUG')
        self.logger.debug(f"JS [{level_str}] {source}:{line} - {message}")


# ============================================================================
# Main Window
# ============================================================================

class SmartFrameWindow(QMainWindow):
    """
    Main application window containing the QtWebEngine browser.
    Runs in fullscreen mode by default.
    """
    
    def __init__(self, logger, windowed=False):
        super().__init__()
        self.logger = logger
        self.windowed = windowed
        
        self._setup_window()
        self._setup_browser()
        self._setup_web_channel()
        
    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle('Smart Frame')
        
        if self.windowed:
            # Windowed mode for testing
            self.setGeometry(100, 100, DISPLAY_WIDTH, DISPLAY_HEIGHT)
        else:
            # Fullscreen mode - remove all window decorations
            self.setWindowFlags(
                Qt.FramelessWindowHint |  # No window frame
                Qt.WindowStaysOnTopHint   # Stay on top
            )
            self.showFullScreen()
        
        # Set fixed size to match display
        self.setFixedSize(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        
        # Hide cursor for kiosk mode
        if not self.windowed:
            self.setCursor(Qt.BlankCursor)
        
        self.logger.info(f"Window created: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}, "
                        f"fullscreen={not self.windowed}")
    
    def _setup_browser(self):
        """Create and configure the WebEngine browser widget."""
        # Create browser widget
        self.browser = QWebEngineView(self)
        
        # Create custom page with logging
        self.page = SmartFramePage(self.logger, self.browser)
        self.browser.setPage(self.page)
        
        # Configure browser settings for performance
        settings = self.browser.settings()
        
        # Enable necessary features
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        # Disable unnecessary features to save memory
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)  # No WebGL needed
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, False)
        settings.setAttribute(QWebEngineSettings.AutoLoadIconsForPage, False)
        settings.setAttribute(QWebEngineSettings.TouchIconsEnabled, False)
        
        # Set up layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # No margins
        layout.setSpacing(0)
        layout.addWidget(self.browser)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Set background to black (prevents white flash on load)
        self.browser.setStyleSheet("background-color: black;")
        self.page.setBackgroundColor(Qt.black)
        
        self.logger.info("Browser widget configured")
    
    def _setup_web_channel(self):
        """Set up QWebChannel for JavaScript bridge."""
        self.channel = QWebChannel(self.page)
        self.chromium_bridge = ChromiumBridge(self.logger, self)
        self.channel.registerObject('chromiumBridge', self.chromium_bridge)
        self.page.setWebChannel(self.channel)
        
        self.logger.info("WebChannel bridge registered")
    
    def load_flask_ui(self):
        """Load the Flask UI in the browser."""
        self.logger.info(f"Loading Flask UI from {FLASK_URL}")
        self.browser.setUrl(QUrl(FLASK_URL))
    
    def reload_page(self):
        """Reload the current page (useful for debugging)."""
        self.browser.reload()
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # F5 = Reload
        if event.key() == Qt.Key_F5:
            self.reload_page()
        # Escape = Exit (only in windowed mode)
        elif event.key() == Qt.Key_Escape and self.windowed:
            self.close()
        # F11 = Toggle fullscreen
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Clean up on window close."""
        self.logger.info("Window closing, cleaning up...")
        
        # Stop any running Chromium processes
        if hasattr(self, 'chromium_bridge'):
            self.chromium_bridge.stop_youtube_music()
        
        event.accept()


# ============================================================================
# Application Controller
# ============================================================================

class SmartFrameApp:
    """
    Main application controller.
    Manages Flask server, Qt application, and handles shutdown.
    """
    
    def __init__(self, debug=False, windowed=False):
        self.debug = debug
        self.windowed = windowed
        self.logger = setup_logging(debug)
        self.flask_thread = None
        self.qt_app = None
        self.window = None
        
    def start_flask(self):
        """Start Flask server in background thread."""
        self.flask_thread = FlaskThread(self.logger)
        self.flask_thread.start()
        
        # Wait for Flask to start (with timeout)
        self.logger.info("Waiting for Flask server to start...")
        max_wait = 10  # seconds
        for i in range(max_wait * 10):
            try:
                import urllib.request
                urllib.request.urlopen(FLASK_URL, timeout=1)
                self.logger.info("Flask server is ready")
                return True
            except Exception:
                sleep(0.1)
        
        self.logger.error("Flask server failed to start within timeout")
        return False
    
    def start_qt(self):
        """Start Qt application and main window."""
        self.logger.info("Initializing Qt application...")
        
        # Create Qt application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName('Smart Frame')
        
        # Create main window
        self.window = SmartFrameWindow(self.logger, self.windowed)
        
        # Load Flask UI after a short delay (ensures Flask is ready)
        QTimer.singleShot(500, self.window.load_flask_ui)
        
        # Show window
        self.window.show()
        
        return True
    
    def run(self):
        """Main entry point - starts everything."""
        self.logger.info("=" * 50)
        self.logger.info("Smart Frame Qt Launcher Starting")
        self.logger.info(f"Debug mode: {self.debug}")
        self.logger.info(f"Windowed mode: {self.windowed}")
        self.logger.info("=" * 50)
        
        # Start Flask server
        if not self.start_flask():
            self.logger.error("Failed to start Flask server, exiting")
            return 1
        
        # Start Qt application
        if not self.start_qt():
            self.logger.error("Failed to start Qt application, exiting")
            return 1
        
        # Run Qt event loop (blocks until window is closed)
        self.logger.info("Starting Qt event loop")
        exit_code = self.qt_app.exec_()
        
        self.logger.info(f"Application exiting with code {exit_code}")
        return exit_code
    
    def shutdown(self):
        """Graceful shutdown handler."""
        self.logger.info("Shutdown requested")
        if self.window:
            self.window.close()
        if self.qt_app:
            self.qt_app.quit()


# ============================================================================
# Signal Handlers
# ============================================================================

def create_signal_handler(app):
    """Create signal handler for graceful shutdown."""
    def handler(signum, frame):
        app.shutdown()
    return handler


# ============================================================================
# Entry Point
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Smart Frame PyQt5 Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run in fullscreen mode (production)
    python3 qt_launcher.py
    
    # Run in windowed mode for testing
    python3 qt_launcher.py --windowed
    
    # Run with debug logging
    python3 qt_launcher.py --debug --windowed
"""
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--windowed', '-w',
        action='store_true',
        help='Run in windowed mode instead of fullscreen'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create application
    app = SmartFrameApp(debug=args.debug, windowed=args.windowed)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, create_signal_handler(app))
    signal.signal(signal.SIGTERM, create_signal_handler(app))
    
    # Run application
    try:
        exit_code = app.run()
    except Exception as e:
        app.logger.exception(f"Unhandled exception: {e}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
