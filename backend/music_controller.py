"""
Music Controller Module
Handles starting and stopping music playback via shell scripts.
"""

import subprocess
import os
from typing import Optional

# Path to scripts directory
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')


class MusicController:
    """Controls music playback through external scripts."""
    
    def __init__(self):
        self._is_playing: bool = False
        self._current_artist: Optional[str] = None
    
    def play_music(self, artist: Optional[str] = None) -> bool:
        """
        Start playing music.
        
        Args:
            artist: Optional artist name to search for
            
        Returns:
            True if music started successfully
        """
        try:
            script_path = os.path.join(SCRIPTS_DIR, 'start_music.sh')
            
            # Build command
            if artist:
                cmd = ['/bin/bash', script_path, artist]
            else:
                cmd = ['/bin/bash', script_path]
            
            # Execute script
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self._is_playing = True
            self._current_artist = artist
            
            return True
        except Exception as e:
            print(f"Error starting music: {e}")
            return False
    
    def stop_music(self) -> bool:
        """
        Stop playing music.
        
        Returns:
            True if music stopped successfully
        """
        try:
            script_path = os.path.join(SCRIPTS_DIR, 'stop_music.sh')
            
            subprocess.run(
                ['/bin/bash', script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            
            self._is_playing = False
            self._current_artist = None
            
            return True
        except Exception as e:
            print(f"Error stopping music: {e}")
            return False
    
    def is_playing(self) -> bool:
        """Check if music is currently playing."""
        return self._is_playing
    
    def get_current_artist(self) -> Optional[str]:
        """Get the currently playing artist, if any."""
        return self._current_artist


# Global instance
_music_controller: Optional[MusicController] = None


def get_music_controller() -> MusicController:
    """Get or create the global MusicController instance."""
    global _music_controller
    if _music_controller is None:
        _music_controller = MusicController()
    return _music_controller
