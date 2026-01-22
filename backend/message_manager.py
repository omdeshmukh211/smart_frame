"""
Message Manager Module
Handles active messages and message storage.
"""

import threading
import os
from datetime import datetime
from typing import Optional

# Path to messages file
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MESSAGES_FILE = os.path.join(DATA_DIR, 'messages.txt')


class MessageManager:
    """Manages messages with expiry and persistent storage."""
    
    def __init__(self, message_timeout: int = 300):
        self._active_message: Optional[str] = None
        self._message_timeout: int = message_timeout
        self._message_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
    
    def set_message(self, message: str) -> bool:
        """
        Set the active message with auto-expiry.
        
        Args:
            message: The message text
            
        Returns:
            True if message was set successfully
        """
        with self._lock:
            # Cancel any existing timer
            self._cancel_timer_internal()
            
            # Set the new message
            self._active_message = message
            
            # Store to file
            self._store_message(message)
            
            # Start expiry timer
            self._message_timer = threading.Timer(
                self._message_timeout,
                self._on_message_timeout
            )
            self._message_timer.daemon = True
            self._message_timer.start()
            
            return True
    
    def get_active_message(self) -> Optional[str]:
        """Get the currently active message, if any."""
        with self._lock:
            return self._active_message
    
    def clear_message(self) -> None:
        """Clear the active message."""
        with self._lock:
            self._active_message = None
            self._cancel_timer_internal()
    
    def _cancel_timer_internal(self) -> None:
        """Internal method to cancel message timer (must hold lock)."""
        if self._message_timer is not None:
            self._message_timer.cancel()
            self._message_timer = None
    
    def _on_message_timeout(self) -> None:
        """Called when message timeout expires."""
        with self._lock:
            self._active_message = None
            self._message_timer = None
    
    def _store_message(self, message: str) -> None:
        """
        Store message to persistent file with timestamp.
        
        Format: YYYY-MM-DD HH:MM | message
        """
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            line = f"{timestamp} | {message}\n"
            
            with open(MESSAGES_FILE, 'a', encoding='utf-8') as f:
                f.write(line)
        except Exception as e:
            print(f"Error storing message: {e}")
    
    def get_message_history(self) -> list:
        """Get all stored messages from file."""
        try:
            if not os.path.exists(MESSAGES_FILE):
                return []
            
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            print(f"Error reading messages: {e}")
            return []


# Global instance
_message_manager: Optional[MessageManager] = None


def get_message_manager(message_timeout: int = 300) -> MessageManager:
    """Get or create the global MessageManager instance."""
    global _message_manager
    if _message_manager is None:
        _message_manager = MessageManager(message_timeout)
    return _message_manager
