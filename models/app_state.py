"""
Application State Model
Centralized state management for Smart Frame.
Thread-safe singleton pattern.
"""

import threading
from typing import Optional, Callable, Dict, Any
from datetime import datetime


class AppState:
    """
    Centralized application state.
    Thread-safe for access from UI and background threads.
    """
    
    # View states
    VIEW_IDLE = 'idle'
    VIEW_HOME = 'home'
    VIEW_PHOTOS = 'photos'
    VIEW_MUSIC = 'music'
    VIEW_SETTINGS = 'settings'
    VIEW_MESSAGES = 'messages'
    VIEW_GAMES = 'games'
    
    def __init__(self, settings: Dict[str, Any]):
        """Initialize application state."""
        self._lock = threading.RLock()
        self._settings = settings
        self._current_view = self.VIEW_IDLE
        self._photo_index = 0
        self._photo_count = 0
        self._music_playing = False
        self._music_paused = False
        self._current_track = None
        self._callbacks = {}
        
        # Runtime state
        self._services_started = False
        self._last_interaction = datetime.now()
        self._idle_timeout = settings.get('idle_timeout', 120)  # 2 minutes default
        
    # ========================================================================
    # Settings
    # ========================================================================
    
    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        with self._lock:
            return self._settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Update a setting value."""
        with self._lock:
            self._settings[key] = value
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        with self._lock:
            return self._settings.copy()
    
    # ========================================================================
    # View State
    # ========================================================================
    
    def get_current_view(self) -> str:
        """Get current view."""
        with self._lock:
            return self._current_view
    
    def set_current_view(self, view: str):
        """Svalid_views = [
                self.VIEW_IDLE, self.VIEW_HOME, self.VIEW_PHOTOS, 
                self.VIEW_MUSIC, self.VIEW_SETTINGS, self.VIEW_MESSAGES,
                self.VIEW_GAMES
            ]
            if view in valid_views:
                old_view = self._current_view
                self._current_view = view
                
                # Update last interaction time if not idle
                if view != self.VIEW_IDLE:
                    self._last_interaction = datetime.now()
                elf.VIEW_PHOTOS, self.VIEW_MUSIC, self.VIEW_SETTINGS]:
                old_view = self._current_view
                self._current_view = view
                if old_view != view:
                    self._trigger_callback('view_changed', view)
    
    # ========================================================================
    # Photo State
    # ========================================================================
    
    def get_photo_index(self) -> int:
        """Get current photo index."""
        with self._lock:
            return self._photo_index
    
    def set_photo_index(self, index: int):
        """Set current photo index."""
        with self._lock:
            self._photo_index = index
            self._trigger_callback('photo_changed', index)
    
    def get_photo_count(self) -> int:
        """Get total photo count."""
        with self._lock:
            return self._photo_count
    
    def set_photo_count(self, count: int):
        """Set total photo count."""
        with self._lock:
            self._photo_count = count
    
    # ========================================================================
    # Music State
    # ========================================================================
    
    def is_music_playing(self) -> bool:
        """Check if music is playing."""
        with self._lock:
            return self._music_playing
    
    def set_music_playing(self, playing: bool):
        """Set music playing state."""
        with self._lock:
            self._music_playing = playing
            if playing:
                self._music_paused = False
            self._trigger_callback('music_state_changed', {'playing': playing, 'paused': self._music_paused})
    
    def is_music_paused(self) -> bool:
        """Check if music is paused."""
        with self._lock:
            return self._music_paused
    
    def set_music_paused(self, paused: bool):
        """Set music paused state."""
        with self._lock:
            self._music_paused = paused
            self._trigger_callback('music_state_changed', {'playing': self._music_playing, 'paused': paused})
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get current track info."""
        with self._lock:
            return self._current_track.copy() if self._current_track else None
    
    def set_current_track(self, track: Optional[Dict[str, Any]]):
        """Set current track info."""
        with self._lock:
            self._current_track = track
            self._trigger_callback('track_changed', track)
    
    # ========================================================================
    # Callbacks
    # ========================================================================
    
    def register_callback(self, event: str, callback: Callable):
        """
        Register a callback for an event.
        
        Events:
        - view_changed: Called when view changes
        - photo_changed: Called when photo index changes
        - music_state_changed: Called when music play/pause state changes
        - track_changed: Called when track changes
        """
        with self._lock:
            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, data=None):
        """Trigger callbacks for an event (must hold lock)."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    import logging
                    logging.getLogger('app_state').error(f"Callback error: {e}")
    
    # ========================================================================
    # Idle Timer
    # ========================================================================
    
    def update_interaction(self):
        """Update last interaction timestamp."""
        with self._lock:
            self._last_interaction = datetime.now()
    
    def get_idle_seconds(self) -> float:
        """Get seconds since last interaction."""
        with self._lock:
            delta = datetime.now() - self._last_interaction
            return delta.total_seconds()
    
    def should_go_idle(self) -> bool:
        """Check if should return to idle view."""
        with self._lock:
            # Don't auto-idle if music is playing or in certain views
            if self._music_playing:
                return False
            if self._current_view in [self.VIEW_IDLE, self.VIEW_MUSIC]:
                return False
            
            return self.get_idle_seconds() > self._idle_timeout
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    def cleanup(self):
        """Cleanup resources."""
        with self._lock:
            self._callbacks.clear()
