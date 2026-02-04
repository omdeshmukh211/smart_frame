#!/usr/bin/env python3
"""
Smart Frame - Native PyQt5 Application
=======================================
Pure PyQt5 implementation with NO web components.
Designed for Raspberry Pi 4 kiosk mode.

Architecture:
- Native Qt widgets only (QLabel, QPushButton, QStackedWidget)
- Background services in QThread for photo/music management
- Direct mpv integration for headless YouTube Music
- Optimized for low-memory ARM devices

Author: Smart Frame Project
Date: February 2026
"""

import sys
import os
import signal
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# Environment Setup (MUST be before PyQt5 imports on Raspberry Pi)
# ============================================================================

# Force software rendering on Raspberry Pi
if sys.platform.startswith('linux'):
    os.environ['LIBGL_ALWAYS_SOFTWARE'] = 'true'
    os.environ['GALLIUM_DRIVER'] = 'llvmpipe'
    os.environ['QT_XCB_GL_INTEGRATION'] = 'none'
    os.environ['QT_QPA_PLATFORM'] = 'xcb'  # X11 backend

# Import PyQt5
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Import our modules
from ui.main_window import MainWindow
from models.app_state import AppState
from config.settings_loader import load_settings

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(debug=False):
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    log_dir = PROJECT_ROOT / 'data'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'smart_frame.log')
        ]
    )
    return logging.getLogger('smart_frame')


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main entry point."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Smart Frame - Native PyQt5 Kiosk')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--windowed', action='store_true', help='Run in window (not fullscreen)')
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.debug)
    logger.info("="*60)
    logger.info("Smart Frame Starting - Native PyQt5 Mode")
    logger.info("="*60)
    
    # Load configuration
    settings = load_settings()
    logger.info(f"Loaded settings: {settings}")
    
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Frame")
    
    # Set global font for touch-friendly UI
    font = QFont("Arial", 14)
    app.setFont(font)
    
    # Create application state
    app_state = AppState(settings)
    
    # Create main window
    main_window = MainWindow(app_state, fullscreen=not args.windowed)
    main_window.show()
    
    # Setup signal handlers for clean shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        app.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Allow Ctrl+C to work
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)
    
    logger.info("Smart Frame ready")
    
    # Run application
    exit_code = app.exec_()
    
    # Cleanup
    logger.info("Smart Frame shutting down")
    app_state.cleanup()
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
