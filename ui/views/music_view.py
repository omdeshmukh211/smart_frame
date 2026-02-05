"""
Music View - Retro Hardware Style
Locked layout music player with search, transport, volume, and dancing bars.
"""

import logging
import random
import subprocess
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QColor, QKeyEvent

from models.app_state import AppState
from services.music_service import MusicService

logger = logging.getLogger(__name__)

# Add VIEW_MENU to AppState if not present
if not hasattr(AppState, 'VIEW_MENU'):
    AppState.VIEW_MENU = 'menu'


class MusicView(QWidget):
    """
    Music player view - Retro Hardware Style.
    
    LOCKED LAYOUT:
    
    SEARCH: ___________
    
    LEFT COLUMN:
    - Transport buttons: ⏮  ⏯  ⏭
    - Volume: VOL [███░░]
    - Back button
    
    RIGHT COLUMN:
    - Song name (large)
    - Artist (smaller)
    - Dancing bars below
    """
    
    # Volume steps (discrete)
    VOLUME_STEPS = 10
    
    def __init__(self, app_state: AppState, music_service: MusicService, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.music_service = music_service
        self.navigate = navigate_callback
        
        self.volume_level = app_state.get_setting('volume', 70) // 10  # 0-10
        self.is_playing = False
        self.is_paused = False
        self.current_track = {'title': 'No track', 'artist': ''}
        self.bar_heights = [3, 5, 4, 6, 3, 5, 4, 6]  # Dancing bars
        self.keyboard_process = None
        
        self._init_ui()
        self._init_timers()
        
        # Listen for music state updates
        app_state.register_callback('music_state_changed', self._on_music_state_changed)
        app_state.register_callback('track_changed', self._on_track_changed)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setStyleSheet("background-color: #000000;")
        self.setFocusPolicy(Qt.StrongFocus)
        
        # We'll use custom painting for the retro look
        # But need a search input
        
        # Create search input (positioned via paintEvent/geometry)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFont(QFont("Courier New", 16))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #101010;
                color: #E0E0E0;
                border: 2px solid #404040;
                padding: 8px 12px;
                font-family: 'Courier New';
            }
            QLineEdit:focus {
                border-color: #808080;
            }
        """)
        self.search_input.setGeometry(60, 50, 400, 45)
        self.search_input.returnPressed.connect(self._search_and_play)
        # Ensure search input gets focus on click
        self.search_input.setFocusPolicy(Qt.ClickFocus)
        
    def _on_search_clicked(self, event):
        """Handle search input click to ensure focus and keyboard."""
        self.search_input.setFocus()
        self.search_input.activateWindow()
        # Call original mousePressEvent
        QLineEdit.mousePressEvent(self.search_input, event)
    
    def _init_timers(self):
        """Initialize timers."""
        # Dancing bars animation (timer-driven, fake)
        self.bars_timer = QTimer()
        self.bars_timer.timeout.connect(self._update_bars)
        
        # Repaint timer
        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(100)
    
    def _update_bars(self):
        """Update dancing bar heights (fake animation)."""
        if self.is_playing and not self.is_paused:
            # Random heights for fake visualization
            self.bar_heights = [random.randint(2, 8) for _ in range(8)]
        else:
            # Flat when paused/stopped
            self.bar_heights = [2] * 8
        self.update()
    
    def paintEvent(self, event):
        """Paint the music interface."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Title
        painter.setPen(QColor(224, 224, 224))
        font = QFont("Courier New", 28, QFont.Bold)
        painter.setFont(font)
        painter.drawText(60, 35, "MUSIC")
        
        # Search label
        painter.setPen(QColor(160, 160, 160))
        font = QFont("Courier New", 14)
        painter.setFont(font)
        painter.drawText(60, 120, "SEARCH:")
        
        # Left column (transport, volume)
        self._draw_transport(painter, 60, 180)
        self._draw_volume(painter, 60, 300)
        self._draw_back_button(painter, 60, 420)
        
        # Right column (track info, bars)
        self._draw_track_info(painter, 400, 180)
        self._draw_dancing_bars(painter, 400, 380)
    
    def _draw_transport(self, painter, x, y):
        """Draw transport buttons."""
        painter.setPen(QColor(160, 160, 160))
        font = QFont("Courier New", 12)
        painter.setFont(font)
        painter.drawText(x, y - 10, "TRANSPORT")
        
        # Button dimensions
        btn_w, btn_h = 80, 60
        spacing = 10
        
        # Previous button
        self._prev_rect = QRectF(x, y, btn_w, btn_h)
        self._draw_button(painter, self._prev_rect, "⏮")
        
        # Play/Pause button
        self._play_rect = QRectF(x + btn_w + spacing, y, btn_w, btn_h)
        play_symbol = "⏸" if (self.is_playing and not self.is_paused) else "▶"
        self._draw_button(painter, self._play_rect, play_symbol)
        
        # Next button
        self._next_rect = QRectF(x + 2 * (btn_w + spacing), y, btn_w, btn_h)
        self._draw_button(painter, self._next_rect, "⏭")
    
    def _draw_button(self, painter, rect, text):
        """Draw a retro button."""
        painter.setPen(QPen(QColor(128, 128, 128), 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(rect)
        
        painter.setPen(QColor(224, 224, 224))
        font = QFont("Courier New", 24)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text)
    
    def _draw_volume(self, painter, x, y):
        """Draw volume control with discrete steps."""
        painter.setPen(QColor(160, 160, 160))
        font = QFont("Courier New", 12)
        painter.setFont(font)
        painter.drawText(x, y - 10, "VOLUME")
        
        # VOL label
        painter.setPen(QColor(224, 224, 224))
        font = QFont("Courier New", 16)
        painter.setFont(font)
        painter.drawText(x, y + 25, "VOL")
        
        # Volume bar
        bar_x = x + 60
        bar_w = 200
        bar_h = 30
        
        # Background
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRect(bar_x, y + 5, bar_w, bar_h)
        
        # Filled blocks (discrete steps)
        block_w = bar_w // self.VOLUME_STEPS
        painter.setPen(Qt.NoPen)
        for i in range(self.VOLUME_STEPS):
            if i < self.volume_level:
                painter.setBrush(QBrush(QColor(200, 200, 180)))  # Filled
            else:
                painter.setBrush(QBrush(QColor(40, 40, 40)))  # Empty
            painter.drawRect(bar_x + i * block_w + 2, y + 7, block_w - 4, bar_h - 4)
        
        # Store rect for click detection
        self._vol_down_rect = QRectF(bar_x - 30, y, 30, bar_h + 10)
        self._vol_up_rect = QRectF(bar_x + bar_w, y, 30, bar_h + 10)
        self._vol_bar_rect = QRectF(bar_x, y + 5, bar_w, bar_h)
        
        # Volume controls
        painter.setPen(QColor(160, 160, 160))
        font = QFont("Courier New", 20)
        painter.setFont(font)
        painter.drawText(self._vol_down_rect, Qt.AlignCenter, "−")
        painter.drawText(self._vol_up_rect, Qt.AlignCenter, "+")
    
    def _draw_back_button(self, painter, x, y):
        """Draw back button."""
        self._back_rect = QRectF(x, y, 100, 50)
        
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(self._back_rect)
        
        painter.setPen(QColor(180, 180, 180))
        font = QFont("Courier New", 14)
        painter.setFont(font)
        painter.drawText(self._back_rect, Qt.AlignCenter, "← BACK")
    
    def _draw_track_info(self, painter, x, y):
        """Draw track name and artist."""
        # Song title (large)
        painter.setPen(QColor(240, 240, 230))
        font = QFont("Courier New", 28, QFont.Bold)
        painter.setFont(font)
        
        title = self.current_track.get('title', 'No track')
        # Truncate if too long
        if len(title) > 25:
            title = title[:22] + "..."
        painter.drawText(x, y + 30, title)
        
        # Artist (smaller)
        painter.setPen(QColor(160, 160, 150))
        font = QFont("Courier New", 18)
        painter.setFont(font)
        
        artist = self.current_track.get('artist', '')
        if len(artist) > 30:
            artist = artist[:27] + "..."
        painter.drawText(x, y + 70, artist)
        
        # Status indicator
        if self.is_playing:
            status = "▶ PLAYING" if not self.is_paused else "⏸ PAUSED"
            color = QColor(100, 200, 100) if not self.is_paused else QColor(200, 200, 100)
        else:
            status = "■ STOPPED"
            color = QColor(150, 150, 150)
        
        painter.setPen(color)
        font = QFont("Courier New", 12)
        painter.setFont(font)
        painter.drawText(x, y + 110, status)
    
    def _draw_dancing_bars(self, painter, x, y):
        """Draw dancing bars visualization."""
        painter.setPen(QColor(100, 100, 100))
        font = QFont("Courier New", 12)
        painter.setFont(font)
        painter.drawText(x, y - 10, "VISUALIZER")
        
        # Bar dimensions
        bar_w = 20
        bar_spacing = 8
        max_h = 80
        
        painter.setPen(Qt.NoPen)
        
        for i, height in enumerate(self.bar_heights):
            bar_h = height * (max_h // 8)
            bx = x + i * (bar_w + bar_spacing)
            by = y + max_h - bar_h
            
            # Color based on playing state
            if self.is_playing and not self.is_paused:
                color = QColor(150, 220, 150)  # Green-ish
            else:
                color = QColor(80, 80, 80)  # Gray
            
            painter.setBrush(QBrush(color))
            painter.drawRect(bx, by, bar_w, bar_h)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks."""
        pos = event.pos()
        
        # Check transport buttons
        if hasattr(self, '_prev_rect') and self._prev_rect.contains(pos.x(), pos.y()):
            self._previous_track()
            return
        if hasattr(self, '_play_rect') and self._play_rect.contains(pos.x(), pos.y()):
            self._toggle_play_pause()
            return
        if hasattr(self, '_next_rect') and self._next_rect.contains(pos.x(), pos.y()):
            self._next_track()
            return
        
        # Check volume controls
        if hasattr(self, '_vol_down_rect') and self._vol_down_rect.contains(pos.x(), pos.y()):
            self._volume_down()
            return
        if hasattr(self, '_vol_up_rect') and self._vol_up_rect.contains(pos.x(), pos.y()):
            self._volume_up()
            return
        if hasattr(self, '_vol_bar_rect') and self._vol_bar_rect.contains(pos.x(), pos.y()):
            # Click on bar to set volume
            rel_x = pos.x() - self._vol_bar_rect.x()
            self.volume_level = int((rel_x / self._vol_bar_rect.width()) * self.VOLUME_STEPS)
            self.volume_level = max(0, min(self.VOLUME_STEPS, self.volume_level))
            self._apply_volume()
            return
        
        # Check back button
        if hasattr(self, '_back_rect') and self._back_rect.contains(pos.x(), pos.y()):
            self._go_back()
            return
    
    def _on_search_clicked(self, event):
        """Handle search box click."""
        QLineEdit.mousePressEvent(self.search_input, event)
        self._show_keyboard()
    
    def _show_keyboard(self):
        """Launch on-screen keyboard if available."""
        try:
            result = subprocess.run(['pgrep', '-x', 'matchbox-keyb'], capture_output=True)
            if result.returncode != 0:
                logger.info("Launching matchbox-keyboard")
                self.keyboard_process = subprocess.Popen(
                    ['matchbox-keyboard'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            logger.debug(f"Keyboard not available: {e}")
    
    def _hide_keyboard(self):
        """Hide on-screen keyboard."""
        try:
            subprocess.run(['pkill', 'matchbox-keyb'], timeout=2)
        except:
            pass
    
    def _search_and_play(self):
        """Search and play music."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        logger.info(f"Searching for: {query}")
        self._hide_keyboard()
        self.music_service.search_and_play(query)
    
    def _toggle_play_pause(self):
        """Toggle play/pause."""
        if self.is_playing:
            if self.is_paused:
                self.music_service.resume()
            else:
                self.music_service.pause()
        self.update()
    
    def _previous_track(self):
        """Previous track."""
        self.music_service.previous()
    
    def _next_track(self):
        """Next track."""
        self.music_service.next()
    
    def _volume_up(self):
        """Increase volume by one step."""
        if self.volume_level < self.VOLUME_STEPS:
            self.volume_level += 1
            self._apply_volume()
    
    def _volume_down(self):
        """Decrease volume by one step."""
        if self.volume_level > 0:
            self.volume_level -= 1
            self._apply_volume()
    
    def _apply_volume(self):
        """Apply current volume level."""
        volume = self.volume_level * 10  # Convert to 0-100
        self.music_service.set_volume(volume)
        self.app_state.set_setting('volume', volume)
        self.update()
    
    def _go_back(self):
        """Go back to menu."""
        self._hide_keyboard()
        if self.navigate:
            self.navigate(AppState.VIEW_MENU)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input."""
        key = event.key()
        
        if key == Qt.Key_Escape:
            self._go_back()
        elif key == Qt.Key_Space:
            self._toggle_play_pause()
        elif key == Qt.Key_Left:
            self._volume_down()
        elif key == Qt.Key_Right:
            self._volume_up()
        elif key == Qt.Key_Up:
            self._previous_track()
        elif key == Qt.Key_Down:
            self._next_track()
        else:
            super().keyPressEvent(event)
    
    def _on_music_state_changed(self, state):
        """Handle music state change from service."""
        self.is_playing = state.get('playing', False)
        self.is_paused = state.get('paused', False)
        
        # Start/stop bars animation
        if self.is_playing and not self.is_paused:
            self.bars_timer.start(150)
        else:
            self.bars_timer.stop()
            self.bar_heights = [2] * 8
        
        self.update()
    
    def _on_track_changed(self, track):
        """Handle track change from service."""
        if track:
            self.current_track = track
        else:
            self.current_track = {'title': 'No track', 'artist': ''}
        self.update()
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Music view activated")
        self.repaint_timer.start(100)
        
        # Update from current state
        self._on_music_state_changed({
            'playing': self.app_state.is_music_playing(),
            'paused': self.app_state.is_music_paused()
        })
        self._on_track_changed(self.app_state.get_current_track())
        self.setFocus()
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Music view deactivated")
        self._hide_keyboard()
        self.bars_timer.stop()
