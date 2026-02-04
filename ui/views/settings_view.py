"""
Settings View
Configuration and system controls.
"""

import logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSpinBox, QComboBox, QCheckBox,
                             QGroupBox, QFormLayout, QMessageBox)
from PyQt5.QtGui import QFont

from models.app_state import AppState
from config.settings_loader import save_settings

logger = logging.getLogger(__name__)


class SettingsView(QWidget):
    """
    Settings and configuration view.
    """
    
    def __init__(self, app_state: AppState, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Photo settings group
        photo_group = QGroupBox("Photo Slideshow")
        photo_group.setFont(QFont("Arial", 16, QFont.Bold))
        photo_layout = QFormLayout(photo_group)
        photo_layout.setSpacing(15)
        
        # Slideshow interval
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(60)
        self.interval_spin.setValue(self.app_state.get_setting('slideshow_interval', 5))
        self.interval_spin.setSuffix(" seconds")
        self.interval_spin.setMinimumHeight(40)
        self.interval_spin.setFont(QFont("Arial", 14))
        photo_layout.addRow("Slide Interval:", self.interval_spin)
        
        # Transition style
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["fade", "instant"])
        self.transition_combo.setCurrentText(self.app_state.get_setting('slideshow_transition', 'fade'))
        self.transition_combo.setMinimumHeight(40)
        self.transition_combo.setFont(QFont("Arial", 14))
        photo_layout.addRow("Transition:", self.transition_combo)
        
        layout.addWidget(photo_group)
        
        # Music settings group
        music_group = QGroupBox("Music Player")
        music_group.setFont(QFont("Arial", 16, QFont.Bold))
        music_layout = QFormLayout(music_group)
        music_layout.setSpacing(15)
        
        # Autoplay
        self.autoplay_check = QCheckBox("Autoplay on startup")
        self.autoplay_check.setChecked(self.app_state.get_setting('music_autoplay', False))
        self.autoplay_check.setFont(QFont("Arial", 14))
        music_layout.addRow("", self.autoplay_check)
        
        # Default volume
        self.volume_spin = QSpinBox()
        self.volume_spin.setMinimum(0)
        self.volume_spin.setMaximum(100)
        self.volume_spin.setValue(self.app_state.get_setting('volume', 70))
        self.volume_spin.setSuffix(" %")
        self.volume_spin.setMinimumHeight(40)
        self.volume_spin.setFont(QFont("Arial", 14))
        music_layout.addRow("Default Volume:", self.volume_spin)
        
        layout.addWidget(music_group)
        
        # System settings group
        system_group = QGroupBox("System")
        system_group.setFont(QFont("Arial", 16, QFont.Bold))
        system_layout = QVBoxLayout(system_group)
        system_layout.setSpacing(15)
        
        # Reboot button
        self.reboot_btn = self._create_system_button("🔄 Reboot System", "#FF9800")
        self.reboot_btn.clicked.connect(self._confirm_reboot)
        system_layout.addWidget(self.reboot_btn)
        
        # Shutdown button
        self.shutdown_btn = self._create_system_button("⏻ Shutdown", "#F44336")
        self.shutdown_btn.clicked.connect(self._confirm_shutdown)
        system_layout.addWidget(self.shutdown_btn)
        
        layout.addWidget(system_group)
        
        # Spacer
        layout.addStretch()
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        # Save button
        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.setMinimumHeight(60)
        self.save_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
        action_layout.addWidget(self.save_btn)
        
        # Home button
        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.setMinimumHeight(60)
        self.home_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.home_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_HOME))
        self.home_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border-radius: 5px;
                padding: 10px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        action_layout.addWidget(self.home_btn)
        
        layout.addLayout(action_layout)
    
    def _create_system_button(self, text: str, color: str) -> QPushButton:
        """Create a system control button."""
        btn = QPushButton(text)
        btn.setMinimumHeight(50)
        btn.setFont(QFont("Arial", 14, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 5px;
                padding: 10px;
                border: none;
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
        """)
        return btn
    
    def _save_settings(self):
        """Save settings to config file."""
        # Update app state
        self.app_state.set_setting('slideshow_interval', self.interval_spin.value())
        self.app_state.set_setting('slideshow_transition', self.transition_combo.currentText())
        self.app_state.set_setting('music_autoplay', self.autoplay_check.isChecked())
        self.app_state.set_setting('volume', self.volume_spin.value())
        
        # Save to file
        success = save_settings(self.app_state.get_all_settings())
        
        if success:
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        else:
            QMessageBox.warning(self, "Save Failed", "Failed to save settings to file.")
    
    def _confirm_reboot(self):
        """Confirm and reboot system."""
        reply = QMessageBox.question(
            self,
            "Confirm Reboot",
            "Are you sure you want to reboot the system?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Rebooting system...")
            import subprocess
            try:
                subprocess.run(['sudo', 'reboot'], check=True)
            except Exception as e:
                logger.error(f"Reboot failed: {e}")
                QMessageBox.warning(self, "Reboot Failed", f"Failed to reboot: {e}")
    
    def _confirm_shutdown(self):
        """Confirm and shutdown system."""
        reply = QMessageBox.question(
            self,
            "Confirm Shutdown",
            "Are you sure you want to shutdown the system?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Shutting down system...")
            import subprocess
            try:
                subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            except Exception as e:
                logger.error(f"Shutdown failed: {e}")
                QMessageBox.warning(self, "Shutdown Failed", f"Failed to shutdown: {e}")
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Settings view activated")
        # Reload current settings
        self.interval_spin.setValue(self.app_state.get_setting('slideshow_interval', 5))
        self.transition_combo.setCurrentText(self.app_state.get_setting('slideshow_transition', 'fade'))
        self.autoplay_check.setChecked(self.app_state.get_setting('music_autoplay', False))
        self.volume_spin.setValue(self.app_state.get_setting('volume', 70))
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Settings view deactivated")
