"""
Music View
Music player interface with playback controls.
"""

import logging
import subprocess
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QSlider, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QFont

from models.app_state import AppState
from services.music_service import MusicService

logger = logging.getLogger(__name__)


class MusicView(QWidget):
    """
    Music player view.
    Search and play YouTube Music via mpv (headless).
    """
    
    def __init__(self, app_state: AppState, music_service: MusicService, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.music_service = music_service
        self.navigate = navigate_callback
        self.keyboard_process = None  # Track keyboard process
        self._init_ui()
        
        # Listen for music state updates
        app_state.register_callback('music_state_changed', self._on_music_state_changed)
        app_state.register_callback('track_changed', self._on_track_changed)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("YouTube Music Player")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a song or artist...")
        self.search_input.setMinimumHeight(50)
        self.search_input.setFont(QFont("Arial", 16))
        self.search_input.returnPressed.connect(self._search_and_play)
        
        # ADDED: Show keyboard when search box is clicked
        self.search_input.mousePressEvent = self._on_search_clicked
        self.search_input.focusInEvent = self._on_search_focus_in
        
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setMinimumHeight(50)
        self.search_btn.setMinimumWidth(120)
        self.search_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.search_btn.clicked.connect(self._search_and_play)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        layout.addSpacing(30)
        
        # Now playing display
        now_playing_label = QLabel("Now Playing:")
        now_playing_label.setFont(QFont("Arial", 18))
        layout.addWidget(now_playing_label)
        
        self.track_title = QLabel("No track playing")
        self.track_title.setFont(QFont("Arial", 22, QFont.Bold))
        self.track_title.setWordWrap(True)
        self.track_title.setAlignment(Qt.AlignCenter)
        self.track_title.setStyleSheet("color: #2196F3; padding: 20px;")
        layout.addWidget(self.track_title)
        
        self.track_artist = QLabel("")
        self.track_artist.setFont(QFont("Arial", 16))
        self.track_artist.setAlignment(Qt.AlignCenter)
        self.track_artist.setStyleSheet("color: #666;")
        layout.addWidget(self.track_artist)
        
        layout.addSpacing(30)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.prev_btn = self._create_control_button("⏮", "Previous")
        self.prev_btn.clicked.connect(self._previous_track)
        controls_layout.addWidget(self.prev_btn)
        
        self.play_pause_btn = self._create_control_button("▶", "Play")
        self.play_pause_btn.setMinimumWidth(100)
        self.play_pause_btn.clicked.connect(self._toggle_play_pause)
        controls_layout.addWidget(self.play_pause_btn)
        
        self.next_btn = self._create_control_button("⏭", "Next")
        self.next_btn.clicked.connect(self._next_track)
        controls_layout.addWidget(self.next_btn)
        
        layout.addLayout(controls_layout)
        
        layout.addSpacing(20)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_label = QLabel("🔊 Volume:")
        volume_label.setFont(QFont("Arial", 14))
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.app_state.get_setting('volume', 70))
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self._volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_value = QLabel(f"{self.volume_slider.value()}%")
        self.volume_value.setFont(QFont("Arial", 14))
        self.volume_value.setMinimumWidth(50)
        volume_layout.addWidget(self.volume_value)
        
        layout.addLayout(volume_layout)
        
        # Spacer
        layout.addStretch()
        
        # Bottom navigation
        nav_layout = QHBoxLayout()
        self.home_btn = self._create_nav_button("🏠 Home")
        self.home_btn.clicked.connect(lambda: self.navigate(AppState.VIEW_HOME))
        nav_layout.addWidget(self.home_btn)
        layout.addLayout(nav_layout)
    
    # ADDED: Keyboard launch methods
    def _on_search_clicked(self, event):
        """Called when search input is clicked."""
        # Call original mouse press event
        QLineEdit.mousePressEvent(self.search_input, event)
        # Show keyboard
        self._show_keyboard()
    
    def _on_search_focus_in(self, event):
        """Called when search input receives focus."""
        # Call original focus in event
        QLineEdit.focusInEvent(self.search_input, event)
        # Show keyboard
        self._show_keyboard()
    
    def _show_keyboard(self):
        """Launch matchbox-keyboard if not already running."""
        try:
            # Check if keyboard is already running
            result = subprocess.run(
                ['pgrep', '-x', 'matchbox-keyb'],
                capture_output=True
            )
            
            if result.returncode != 0:  # Not running
                logger.info("Launching matchbox-keyboard")
                self.keyboard_process = subprocess.Popen(
                    ['matchbox-keyboard'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                logger.debug("Keyboard already running")
        except Exception as e:
            logger.error(f"Failed to launch keyboard: {e}")
    
    def _hide_keyboard(self):
        """Hide the on-screen keyboard."""
        try:
            subprocess.run(['pkill', 'matchbox-keyb'], timeout=2)
            logger.info("Keyboard hidden")
        except Exception as e:
            logger.error(f"Failed to hide keyboard: {e}")
    
    def _create_control_button(self, symbol: str, tooltip: str) -> QPushButton:
        """Create a playback control button."""
        btn = QPushButton(symbol)
        btn.setToolTip(tooltip)
        btn.setMinimumHeight(80)
        btn.setMinimumWidth(80)
        btn.setFont(QFont("Arial", 24))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 40px;
                border: none;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        return btn
    
    def _create_nav_button(self, text: str) -> QPushButton:
        """Create a navigation button."""
        btn = QPushButton(text)
        btn.setMinimumHeight(60)
        btn.setMinimumWidth(150)
        btn.setFont(QFont("Arial", 16, QFont.Bold))
        btn.setStyleSheet("""
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
        return btn
    
    def _search_and_play(self):
        """Search for and play a song."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        logger.info(f"Searching for: {query}")
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        
        # ADDED: Hide keyboard when searching
        self._hide_keyboard()
        
        # Search and play in background
        self.music_service.search_and_play(query)
        
        # Re-enable button after short delay
        QTimer.singleShot(2000, lambda: (
            self.search_btn.setEnabled(True),
            self.search_btn.setText("🔍 Search")
        ))
    
    def _toggle_play_pause(self):
        """Toggle play/pause."""
        if self.app_state.is_music_playing():
            if self.app_state.is_music_paused():
                self.music_service.resume()
            else:
                self.music_service.pause()
        # If nothing playing, try to play something
    
    def _previous_track(self):
        """Play previous track."""
        self.music_service.previous()
    
    def _next_track(self):
        """Play next track."""
        self.music_service.next()
    
    def _volume_changed(self, value):
        """Handle volume slider change."""
        self.volume_value.setText(f"{value}%")
        self.music_service.set_volume(value)
        self.app_state.set_setting('volume', value)
    
    def _on_music_state_changed(self, state):
        """Handle music state change."""
        playing = state.get('playing', False)
        paused = state.get('paused', False)
        
        if playing and not paused:
            self.play_pause_btn.setText("⏸")
            self.play_pause_btn.setToolTip("Pause")
        else:
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setToolTip("Play")
    
    def _on_track_changed(self, track):
        """Handle track change."""
        if track:
            self.track_title.setText(track.get('title', 'Unknown'))
            self.track_artist.setText(track.get('artist', ''))
        else:
            self.track_title.setText("No track playing")
            self.track_artist.setText("")
    
    def on_activate(self):
        """Called when view becomes active."""
        logger.debug("Music view activated")
        # Update UI to current state
        self._on_music_state_changed({
            'playing': self.app_state.is_music_playing(),
            'paused': self.app_state.is_music_paused()
        })
        self._on_track_changed(self.app_state.get_current_track())
    
    def on_deactivate(self):
        """Called when view becomes inactive."""
        logger.debug("Music view deactivated")
        # ADDED: Hide keyboard when leaving view
        self._hide_keyboard()
        # Music continues playing in background