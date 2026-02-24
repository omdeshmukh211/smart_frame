"""
Music View - Retro Hardware Style
Locked layout music player with search, transport, volume, and dancing bars.
"""

import logging
import random
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
    
    # Keyboard layout for search
    KEYBOARD_ROWS = [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
    ]
    
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
        self.keyboard_visible = False  # Native on-screen keyboard visibility
        self.caps_lock = False  # Caps lock state
        
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
        # Make search input read-only to prevent system keyboard
        self.search_input.setReadOnly(True)
        self.search_input.mousePressEvent = self._on_search_input_clicked
        
    def _on_search_input_clicked(self, event):
        """Handle click on search input to show native keyboard."""
        self.keyboard_visible = True
        self.update()
    
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
        
        # Draw native keyboard if visible
        if self.keyboard_visible:
            self._draw_keyboard(painter)
    
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
    
    def _draw_keyboard(self, painter):
        """Draw the native on-screen keyboard for search."""
        w, h = self.width(), self.height()
        
        # Keyboard background (semi-transparent overlay)
        painter.setBrush(QBrush(QColor(0, 0, 0, 230)))
        painter.setPen(Qt.NoPen)
        keyboard_height = 280
        keyboard_y = h - keyboard_height
        painter.drawRect(0, keyboard_y, w, keyboard_height)
        
        # Border at top of keyboard
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawLine(0, keyboard_y, w, keyboard_y)
        
        # Key dimensions
        key_w = 45
        key_h = 45
        spacing = 5
        
        start_y = keyboard_y + 15
        
        # Store key rects for click detection
        self._keyboard_keys = {}
        
        # Draw letter/number rows
        for row_idx, row in enumerate(self.KEYBOARD_ROWS):
            row_width = len(row) * (key_w + spacing) - spacing
            start_x = (w - row_width) // 2
            y = start_y + row_idx * (key_h + spacing)
            
            for col_idx, letter in enumerate(row):
                x = start_x + col_idx * (key_w + spacing)
                display_letter = letter if self.caps_lock or letter.isdigit() else letter.lower()
                self._draw_key(painter, x, y, key_w, key_h, display_letter, QColor(60, 60, 60))
                self._keyboard_keys[letter] = QRectF(x, y, key_w, key_h)
        
        # Bottom row: CAPS, SPACE, BACKSPACE, SEARCH
        bottom_y = start_y + 4 * (key_h + spacing)
        
        # Calculate positions for bottom row
        total_bottom_width = 70 + spacing + 200 + spacing + 70 + spacing + 100  # CAPS + SPACE + BACK + SEARCH
        bottom_start_x = (w - total_bottom_width) // 2
        
        # CAPS LOCK button
        caps_color = QColor(100, 150, 100) if self.caps_lock else QColor(60, 60, 60)
        self._draw_key(painter, bottom_start_x, bottom_y, 70, key_h, "CAPS", caps_color)
        self._caps_rect = QRectF(bottom_start_x, bottom_y, 70, key_h)
        
        # SPACE button
        space_x = bottom_start_x + 70 + spacing
        self._draw_key(painter, space_x, bottom_y, 200, key_h, "SPACE", QColor(60, 60, 60))
        self._space_rect = QRectF(space_x, bottom_y, 200, key_h)
        
        # BACKSPACE button
        back_x = space_x + 200 + spacing
        self._draw_key(painter, back_x, bottom_y, 70, key_h, "⌫", QColor(120, 80, 80))
        self._backspace_rect = QRectF(back_x, bottom_y, 70, key_h)
        
        # SEARCH button
        search_x = back_x + 70 + spacing
        self._draw_key(painter, search_x, bottom_y, 100, key_h, "SEARCH", QColor(80, 120, 80))
        self._search_btn_rect = QRectF(search_x, bottom_y, 100, key_h)
        
        # Close keyboard button (X) at top right of keyboard
        close_x = w - 50
        close_y = keyboard_y + 10
        self._draw_key(painter, close_x, close_y, 40, 35, "✕", QColor(120, 60, 60))
        self._close_kb_rect = QRectF(close_x, close_y, 40, 35)
    
    def _draw_key(self, painter, x, y, w, h, text, color):
        """Draw a keyboard key."""
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), 5, 5)
        
        painter.setPen(QColor(240, 240, 240))
        font_size = 10 if len(text) > 2 else 14
        font = QFont("Courier New", font_size, QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(x), int(y), int(w), int(h), Qt.AlignCenter, text)
    
    def _handle_keyboard_click(self, pos):
        """Handle clicks on the native keyboard. Returns True if handled."""
        if not self.keyboard_visible:
            return False
        
        x, y = pos.x(), pos.y()
        
        # Check close button
        if hasattr(self, '_close_kb_rect') and self._close_kb_rect.contains(x, y):
            self.keyboard_visible = False
            self.update()
            return True
        
        # Check letter/number keys
        if hasattr(self, '_keyboard_keys'):
            for letter, rect in self._keyboard_keys.items():
                if rect.contains(x, y):
                    current_text = self.search_input.text()
                    char = letter if self.caps_lock or letter.isdigit() else letter.lower()
                    self.search_input.setText(current_text + char)
                    self.update()
                    return True
        
        # Check CAPS key
        if hasattr(self, '_caps_rect') and self._caps_rect.contains(x, y):
            self.caps_lock = not self.caps_lock
            self.update()
            return True
        
        # Check SPACE key
        if hasattr(self, '_space_rect') and self._space_rect.contains(x, y):
            current_text = self.search_input.text()
            self.search_input.setText(current_text + ' ')
            self.update()
            return True
        
        # Check BACKSPACE key
        if hasattr(self, '_backspace_rect') and self._backspace_rect.contains(x, y):
            current_text = self.search_input.text()
            if current_text:
                self.search_input.setText(current_text[:-1])
            self.update()
            return True
        
        # Check SEARCH key
        if hasattr(self, '_search_btn_rect') and self._search_btn_rect.contains(x, y):
            self.keyboard_visible = False
            self._search_and_play()
            self.update()
            return True
        
        return False
    
    def mousePressEvent(self, event):
        """Handle mouse clicks."""
        pos = event.pos()
        
        # Check keyboard first if visible
        if self.keyboard_visible:
            if self._handle_keyboard_click(pos):
                return
        
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
    
    def _search_and_play(self):
        """Search and play music."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        logger.info(f"Searching for: {query}")
        self.keyboard_visible = False
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
        self.keyboard_visible = False
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
        self.keyboard_visible = False
        self.bars_timer.stop()
