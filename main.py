#!/usr/bin/env python3
"""
Smart Frame - Native PyQt5 Application
Pure native widgets - no web dependencies, no Flask, no QtWebEngine.

Usage:
    python3 main.py [--fullscreen] [--debug]

Options:
    --fullscreen    Launch in fullscreen kiosk mode
    --debug         Enable debug logging
"""

import sys
import os
import logging
import argparse
import faulthandler
import signal

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Ensure data dir exists early so crash logs can be written
data_dir_early = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(data_dir_early, exist_ok=True)
_faulthandler_log_path = os.path.join(data_dir_early, 'faulthandler.log')
_faulthandler_file = open(_faulthandler_log_path, 'a+')
faulthandler.enable(file=_faulthandler_file)
# Register handlers for common fatal signals
for _sig in (signal.SIGILL, signal.SIGSEGV, signal.SIGABRT, signal.SIGFPE):
    try:
        faulthandler.register(_sig, file=_faulthandler_file, all_threads=True)
    except Exception:
        pass

# PyQt5 imports - NATIVE WIDGETS ONLY
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Application imports
from models.app_state import AppState
from ui.main_window import MainWindow
from config.settings_loader import load_settings
from backend.git_updater import start_git_updater, stop_git_updater
from backend.scheduled_message_manager import start_scheduled_message_manager


def setup_logging(debug=False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Ensure data directory exists
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(data_dir, 'smart_frame.log'))
        ]
    )
    
    logger = logging.getLogger('smart_frame')
    logger.info("=" * 60)
    logger.info("Smart Frame - Native PyQt5 Application Starting")
    logger.info("=" * 60)
    
    return logger


def main():
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Smart Frame - Native PyQt5')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Launch in fullscreen kiosk mode')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.debug)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Frame")
    app.setOrganizationName("SmartFrame")
    
    # Set application-wide style
    app.setStyle('Fusion')  # Consistent look across platforms
    
    # Disable screen blanking (for kiosk mode)
    if args.fullscreen:
        logger.info("Fullscreen mode enabled")
    
    # Load settings and create application state
    settings = load_settings()
    app_state = AppState(settings)
    
    # Create and show main window
    window = MainWindow(app_state, fullscreen=args.fullscreen)
    window.show()
    
    # Start background services
    # Git auto-updater: pulls from remote every 3 minutes
    try:
        git_updater = start_git_updater(PROJECT_ROOT)
        logger.info("Git auto-updater started")
    except Exception as e:
        logger.error(f"Failed to start git updater: {e}")
    
    # Scheduled message manager: checks for due messages and displays them
    def on_scheduled_message(msg):
        """Callback when a scheduled message is due."""
        title = msg.get('from', 'Message')
        body = msg.get('text', '')
        logger.info(f"Scheduled message due: {title} - {body}")
        # Show message via the overlay (must be called from main thread)
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            window, 'show_system_message',
            Qt.QueuedConnection,
            Q_ARG(str, title),
            Q_ARG(str, body)
        )
    
    try:
        scheduled_manager = start_scheduled_message_manager(on_scheduled_message)
        logger.info("Scheduled message manager started")
    except Exception as e:
        logger.error(f"Failed to start scheduled message manager: {e}")
    
    logger.info("Main window created and displayed")
    logger.info(f"Resolution: {window.DISPLAY_WIDTH}x{window.DISPLAY_HEIGHT}")
    logger.info("Application ready")
    
    # Run application event loop
    exit_code = app.exec_()
    
    # Stop background services
    try:
        stop_git_updater()
    except Exception as e:
        logger.error(f"Error stopping git updater: {e}")
    
    logger.info("Application shutting down")
    logger.info("=" * 60)
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
