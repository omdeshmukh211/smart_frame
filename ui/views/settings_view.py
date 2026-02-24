"""
Settings View - Retro Hardware Style
Text-based settings with discrete bar controls.
"""

import logging
import subprocess
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton
from PyQt5.QtGui import QFont, QKeyEvent, QPainter, QColor, QPen, QBrush

from models.app_state import AppState
from config.settings_loader import save_settings

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class SettingsView(QWidget):
    """
    Settings view - Retro Hardware Style.
    
    SETTINGS
    ▶ Volume
      Brightness
      Wi-Fi
    
    VOLUME / BRIGHTNESS:
    - Bar-style discrete steps: [ █ █ █ ░ ░ ]
    - Left / Right adjusts
    
    WI-FI:
    - List of networks with signal bars
    - Connected network marked
    """
    
    MENU_ITEMS = [
        ('Volume', 'volume'),
        ('Brightness', 'brightness'),
        ('Wi-Fi', 'wifi'),
    ]
    
    STEPS = 10
    
    def __init__(self, app_state: AppState, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        
        self.selected_index = 0
        self.editing_setting = None  # Which setting is being edited
        self.volume_level = app_state.get_setting('volume', 70) // 10
        self.brightness_level = app_state.get_setting('brightness', 80) // 10
        self.wifi_networks = []
        self.wifi_selected = 0
        
        self._init_ui()
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setStyleSheet("background-color: #000000;")
        
        # Close button in top-right corner (consistent with other views)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(50, 50)
        self.close_btn.setFont(QFont("Arial", 20, QFont.Bold))
        self.close_btn.clicked.connect(lambda: self._go_back())
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 25px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        # We use paintEvent for full control
    
    def paintEvent(self, event):
        """Paint the settings interface."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Title
        painter.setPen(QColor(224, 224, 224))
        font = QFont("Courier New", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(60, 80, "SETTINGS")
        
        if self.editing_setting:
            self._draw_setting_editor(painter)
        else:
            self._draw_menu(painter)
        
        # Hint at bottom
        if self.editing_setting:
            hint = "[←/→] Adjust   [BACK] Return"
        else:
            hint = "[TAP] Edit   [BACK] Menu"
        
        painter.setPen(QColor(96, 96, 96))
        font = QFont("Courier New", 14)
        painter.setFont(font)
        painter.drawText(0, self.height() - 40, self.width(), 30, Qt.AlignCenter, hint)
    
    def resizeEvent(self, event):
        """Handle resize to position close button."""
        super().resizeEvent(event)
        # Position close button in top-right corner
        self.close_btn.move(self.width() - 60 - 50, 10)
    
    def _draw_menu(self, painter):
        """Draw the settings menu list."""
        y = 150
        
        for i, (name, _) in enumerate(self.MENU_ITEMS):
            if i == self.selected_index:
                text = f"▶ {name}"
                color = QColor(255, 255, 255)
            else:
                text = f"  {name}"
                color = QColor(128, 128, 128)
            
            painter.setPen(color)
            font = QFont("Courier New", 24)
            painter.setFont(font)
            painter.drawText(60, y, text)
            
            y += 50
    
    def _draw_setting_editor(self, painter):
        """Draw the setting editor view."""
        if self.editing_setting == 'volume':
            self._draw_bar_editor(painter, "VOLUME", self.volume_level)
        elif self.editing_setting == 'brightness':
            self._draw_bar_editor(painter, "BRIGHTNESS", self.brightness_level)
        elif self.editing_setting == 'wifi':
            self._draw_wifi_editor(painter)
    
    def _draw_bar_editor(self, painter, label, level):
        """Draw a bar-style discrete editor."""
        y = 180
        
        # Label
        painter.setPen(QColor(160, 160, 160))
        font = QFont("Courier New", 18)
        painter.setFont(font)
        painter.drawText(60, y, label)
        
        y += 40
        
        # Bar
        bar_x = 60
        bar_w = 400
        bar_h = 50
        block_w = bar_w // self.STEPS
        
        # Background
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRect(bar_x, y, bar_w, bar_h)
        
        # Blocks
        painter.setPen(Qt.NoPen)
        for i in range(self.STEPS):
            if i < level:
                painter.setBrush(QBrush(QColor(200, 200, 180)))
            else:
                painter.setBrush(QBrush(QColor(40, 40, 40)))
            painter.drawRect(bar_x + i * block_w + 4, y + 4, block_w - 8, bar_h - 8)
        
        # Value display
        y += 70
        painter.setPen(QColor(224, 224, 224))
        font = QFont("Courier New", 24)
        painter.setFont(font)
        painter.drawText(60, y, f"{level * 10}%")
        
        # Instructions
        y += 60
        painter.setPen(QColor(128, 128, 128))
        font = QFont("Courier New", 16)
        painter.setFont(font)
        painter.drawText(60, y, "[ − ]              [ + ]")
        
        # Store rects for click detection
        self._dec_rect = QRectF(60, y - 25, 60, 40)
        self._inc_rect = QRectF(bar_x + bar_w - 60, y - 25, 60, 40)
        self._bar_rect = QRectF(bar_x, 220, bar_w, bar_h)
    
    def _draw_wifi_editor(self, painter):
        """Draw WiFi network list."""
        y = 180
        
        # Scan networks if empty
        if not self.wifi_networks:
            self._scan_wifi()
        
        if not self.wifi_networks:
            painter.setPen(QColor(128, 128, 128))
            font = QFont("Courier New", 18)
            painter.setFont(font)
            painter.drawText(60, y, "No networks found")
            painter.drawText(60, y + 40, "Scanning...")
            return
        
        for i, network in enumerate(self.wifi_networks[:8]):
            ssid = network.get('ssid', 'Unknown')
            signal = network.get('signal', 0)
            connected = network.get('connected', False)
            
            if i == self.wifi_selected:
                prefix = "▶ "
                color = QColor(255, 255, 255)
            else:
                prefix = "  "
                color = QColor(128, 128, 128)
            
            # SSID
            if len(ssid) > 20:
                ssid = ssid[:17] + "..."
            
            # Signal bars
            bars = self._signal_to_bars(signal)
            
            # Connected indicator
            status = " ✓" if connected else ""
            
            text = f"{prefix}{ssid:<22} {bars}{status}"
            
            painter.setPen(color)
            font = QFont("Courier New", 18)
            painter.setFont(font)
            painter.drawText(60, y, text)
            
            y += 40
    
    def _signal_to_bars(self, signal):
        """Convert signal strength to bar display."""
        if signal >= 80:
            return "████"
        elif signal >= 60:
            return "███░"
        elif signal >= 40:
            return "██░░"
        elif signal >= 20:
            return "█░░░"
        else:
            return "░░░░"
    
    def _scan_wifi(self):
        """Scan for WiFi networks."""
        self.wifi_networks = []
        
        try:
            # Try nmcli on Linux
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,SIGNAL,ACTIVE', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 3 and parts[0]:
                            self.wifi_networks.append({
                                'ssid': parts[0],
                                'signal': int(parts[1]) if parts[1].isdigit() else 0,
                                'connected': parts[2] == 'yes'
                            })
        except Exception as e:
            logger.debug(f"WiFi scan not available: {e}")
            # Add dummy data for testing
            self.wifi_networks = [
                {'ssid': 'Home_Network', 'signal': 85, 'connected': True},
                {'ssid': 'Neighbor_5G', 'signal': 45, 'connected': False},
                {'ssid': 'Guest_WiFi', 'signal': 30, 'connected': False},
            ]
    
    def mousePressEvent(self, event):
        """Handle mouse clicks."""
        pos = event.pos()
        
        if self.editing_setting in ('volume', 'brightness'):
            # Check increment/decrement buttons
            if hasattr(self, '_dec_rect') and self._dec_rect.contains(pos.x(), pos.y()):
                self._adjust_level(-1)
                return
            if hasattr(self, '_inc_rect') and self._inc_rect.contains(pos.x(), pos.y()):
                self._adjust_level(1)
                return
            if hasattr(self, '_bar_rect') and self._bar_rect.contains(pos.x(), pos.y()):
                # Click on bar to set level
                rel_x = pos.x() - self._bar_rect.x()
                level = int((rel_x / self._bar_rect.width()) * self.STEPS)
                level = max(0, min(self.STEPS, level))
                if self.editing_setting == 'volume':
                    self.volume_level = level
                else:
                    self.brightness_level = level
                self._apply_setting()
                return
        
        if not self.editing_setting:
            # Check if clicked on a menu item
            y = 125
            for i, _ in enumerate(self.MENU_ITEMS):
                item_rect = QRectF(60, y, 400, 45)
                if item_rect.contains(pos.x(), pos.y()):
                    self.selected_index = i
                    self._enter_setting()
                    return
                y += 50
        
        # Click elsewhere goes back
        self._go_back()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        key = event.key()
        
        if self.editing_setting:
            if key == Qt.Key_Escape or key == Qt.Key_Backspace:
                self._exit_setting()
            elif key == Qt.Key_Left:
                self._adjust_level(-1)
            elif key == Qt.Key_Right:
                self._adjust_level(1)
            elif key == Qt.Key_Up and self.editing_setting == 'wifi':
                if self.wifi_networks:
                    self.wifi_selected = (self.wifi_selected - 1) % len(self.wifi_networks)
                    self.update()
            elif key == Qt.Key_Down and self.editing_setting == 'wifi':
                if self.wifi_networks:
                    self.wifi_selected = (self.wifi_selected + 1) % len(self.wifi_networks)
                    self.update()
            elif key in (Qt.Key_Return, Qt.Key_Enter) and self.editing_setting == 'wifi':
                self._connect_wifi()
        else:
            if key == Qt.Key_Up:
                self.selected_index = (self.selected_index - 1) % len(self.MENU_ITEMS)
                self.update()
            elif key == Qt.Key_Down:
                self.selected_index = (self.selected_index + 1) % len(self.MENU_ITEMS)
                self.update()
            elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                self._enter_setting()
            elif key == Qt.Key_Escape:
                self._go_back()
            else:
                super().keyPressEvent(event)
    
    def _enter_setting(self):
        """Enter a setting for editing."""
        _, setting_id = self.MENU_ITEMS[self.selected_index]
        self.editing_setting = setting_id
        
        if setting_id == 'wifi':
            self.wifi_selected = 0
            self._scan_wifi()
        
        self.update()
    
    def _exit_setting(self):
        """Exit setting editing."""
        self._save_settings()
        self.editing_setting = None
        self.update()
    
    def _adjust_level(self, delta):
        """Adjust the current setting level."""
        if self.editing_setting == 'volume':
            self.volume_level = max(0, min(self.STEPS, self.volume_level + delta))
        elif self.editing_setting == 'brightness':
            self.brightness_level = max(0, min(self.STEPS, self.brightness_level + delta))
        
        self._apply_setting()
        self.update()
    
    def _apply_setting(self):
        """Apply the current setting immediately."""
        if self.editing_setting == 'volume':
            volume = self.volume_level * 10
            self.app_state.set_setting('volume', volume)
            # Apply system volume if possible
            try:
                subprocess.run(['amixer', 'sset', 'Master', f'{volume}%'], 
                             capture_output=True, timeout=2)
            except:
                pass
        elif self.editing_setting == 'brightness':
            brightness = self.brightness_level * 10
            self.app_state.set_setting('brightness', brightness)
            # Apply system brightness if possible
            try:
                subprocess.run(['brightnessctl', 'set', f'{brightness}%'],
                             capture_output=True, timeout=2)
            except:
                pass
    
    def _connect_wifi(self):
        """Connect to selected WiFi network."""
        if not self.wifi_networks or self.wifi_selected >= len(self.wifi_networks):
            return
        
        network = self.wifi_networks[self.wifi_selected]
        ssid = network.get('ssid', '')
        
        logger.info(f"Connecting to WiFi: {ssid}")
        
        try:
            subprocess.run(['nmcli', 'device', 'wifi', 'connect', ssid],
                         capture_output=True, timeout=10)
            self._scan_wifi()
            self.update()
        except Exception as e:
            logger.error(f"WiFi connection failed: {e}")
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            settings = self.app_state.get_all_settings()
            save_settings(settings)
            logger.info("Settings saved")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def _go_back(self):
        """Go back."""
        if self.editing_setting:
            self._exit_setting()
        elif self.navigate:
            self.navigate(AppState.VIEW_MENU)
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Settings view activated")
        self.selected_index = 0
        self.editing_setting = None
        self.volume_level = self.app_state.get_setting('volume', 70) // 10
        self.brightness_level = self.app_state.get_setting('brightness', 80) // 10
        self.setFocus()
        self.update()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Settings view deactivated")
        self._save_settings()
