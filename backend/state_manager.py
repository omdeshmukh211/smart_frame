"""
State Manager Module
Handles application state and timers.
"""

import threading
import time
from typing import Optional, Callable

# Import constants
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.constants import STATE_IDLE, STATE_CLOCK, STATE_MUSIC


class StateManager:
    """Manages the current system state and associated timers."""
    
    def __init__(self, clock_timeout: int = 120):
        self._current_state: str = STATE_IDLE
        self._clock_timeout: int = clock_timeout
        self._clock_timer: Optional[threading.Timer] = None
        self._state_change_callback: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()
    
    def set_state_change_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback to be called when state changes."""
        self._state_change_callback = callback
    
    def get_state(self) -> str:
        """Get the current system state."""
        with self._lock:
            return self._current_state
    
    def set_state(self, new_state: str) -> bool:
        """
        Set the system state.
        
        Args:
            new_state: One of STATE_IDLE, STATE_CLOCK, STATE_MUSIC
            
        Returns:
            True if state was changed, False otherwise
        """
        with self._lock:
            if new_state not in [STATE_IDLE, STATE_CLOCK, STATE_MUSIC]:
                return False
            
            old_state = self._current_state
            self._current_state = new_state
            
            # Cancel any existing clock timer
            self._cancel_clock_timeout_internal()
            
            # Start clock timeout if entering CLOCK state
            if new_state == STATE_CLOCK:
                self._start_clock_timeout_internal()
            
            # Notify callback if state changed
            if old_state != new_state and self._state_change_callback:
                self._state_change_callback(new_state)
            
            return True
    
    def start_clock_timeout(self) -> None:
        """Start the clock timeout timer."""
        with self._lock:
            self._start_clock_timeout_internal()
    
    def _start_clock_timeout_internal(self) -> None:
        """Internal method to start clock timeout (must hold lock)."""
        self._cancel_clock_timeout_internal()
        self._clock_timer = threading.Timer(
            self._clock_timeout,
            self._on_clock_timeout
        )
        self._clock_timer.daemon = True
        self._clock_timer.start()
    
    def cancel_clock_timeout(self) -> None:
        """Cancel any active clock timeout timer."""
        with self._lock:
            self._cancel_clock_timeout_internal()
    
    def _cancel_clock_timeout_internal(self) -> None:
        """Internal method to cancel clock timeout (must hold lock)."""
        if self._clock_timer is not None:
            self._clock_timer.cancel()
            self._clock_timer = None
    
    def _on_clock_timeout(self) -> None:
        """Called when clock timeout expires."""
        with self._lock:
            if self._current_state == STATE_CLOCK:
                self._current_state = STATE_IDLE
                self._clock_timer = None
                if self._state_change_callback:
                    self._state_change_callback(STATE_IDLE)


# Global instance
_state_manager: Optional[StateManager] = None


def get_state_manager(clock_timeout: int = 120) -> StateManager:
    """Get or create the global StateManager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager(clock_timeout)
    return _state_manager
