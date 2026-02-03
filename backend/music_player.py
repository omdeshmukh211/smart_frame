"""
YouTube Music Player Module
Lightweight, headless music player using yt-dlp and mpv for audio playback.
Replaces Chromium-based YouTube Music with a resource-efficient solution.
"""

import subprocess
import threading
import json
import time
import os
import logging
from typing import Optional, Dict, List
from queue import Queue
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeMusicPlayer:
    """
    Headless YouTube music player using yt-dlp for search/streaming and mpv for playback.
    
    Features:
    - Search YouTube and play top result
    - Play/pause/resume controls
    - Next/previous track navigation
    - Track queue management
    - Auto-play related tracks
    - Low resource usage (no browser needed)
    """
    
    def __init__(self):
        """Initialize the music player."""
        self.mpv_process: Optional[subprocess.Popen] = None
        self.current_track: Optional[Dict] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.track_queue: List[Dict] = []
        self.track_history: List[Dict] = []
        self.current_queue_index: int = -1
        self._monitor_thread: Optional[threading.Thread] = None
        self._should_stop_monitoring: bool = False
        self._lock = threading.Lock()
        
        # Check if required tools are available
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if yt-dlp and mpv are installed."""
        try:
            subprocess.run(['yt-dlp', '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("yt-dlp not found. Please install: pip install yt-dlp")
        
        try:
            subprocess.run(['mpv', '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("mpv not found. Please install: sudo apt-get install mpv")
    
    def search_and_play(self, query: str) -> bool:
        """
        Search YouTube for a song/artist and play the top result.
        
        Args:
            query: Search query (song name, artist, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Searching YouTube for: {query}")
            
            # Use yt-dlp to search YouTube and get the top result
            search_cmd = [
                'yt-dlp',
                '--default-search', 'ytsearch1',  # Search YouTube, get 1 result
                '--skip-download',  # Don't download, just get info
                '--print', '%(id)s|%(title)s|%(uploader)s|%(duration)s',
                f'ytsearch1:{query}'
            ]
            
            result = subprocess.run(
                search_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                logger.error(f"Search failed: {result.stderr}")
                return False
            
            # Parse the result
            output = result.stdout.strip()
            if not output:
                logger.error("No results found")
                return False
            
            parts = output.split('|')
            if len(parts) < 4:
                logger.error(f"Unexpected output format: {output}")
                return False
            
            video_id, title, uploader, duration = parts[0], parts[1], parts[2], parts[3]
            
            # Create track info
            track = {
                'id': video_id,
                'title': title,
                'artist': uploader,
                'duration': duration,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'query': query
            }
            
            logger.info(f"Found: {title} by {uploader}")
            
            # Play the track
            return self._play_track(track)
            
        except subprocess.TimeoutExpired:
            logger.error("Search timed out")
            return False
        except Exception as e:
            logger.error(f"Search error: {e}")
            return False
    
    def _play_track(self, track: Dict) -> bool:
        """
        Play a specific track.
        
        Args:
            track: Track information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Stop current playback
            self._stop_mpv()
            
            logger.info(f"Playing: {track['title']}")
            
            # Start mpv with the YouTube URL
            # mpv will use yt-dlp internally to stream audio
            self.mpv_process = subprocess.Popen(
                [
                    'mpv',
                    '--no-video',  # Audio only
                    '--no-terminal',  # No terminal output
                    '--really-quiet',  # Suppress messages
                    '--audio-display=no',  # No album art window
                    '--ytdl-format=bestaudio',  # Best audio quality
                    '--volume=100',  # Set volume (system controls overall volume)
                    track['url']
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.PIPE
            )
            
            # Update state
            with self._lock:
                self.current_track = track
                self.is_playing = True
                self.is_paused = False
                
                # Add to history
                if not self.track_history or self.track_history[-1]['id'] != track['id']:
                    self.track_history.append(track)
                
                # Update queue index
                if track in self.track_queue:
                    self.current_queue_index = self.track_queue.index(track)
            
            # Start monitoring thread
            self._start_monitor()
            
            return True
            
        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Pause playback.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.mpv_process or not self.is_playing or self.is_paused:
                return False
            
            # Send pause command to mpv via stdin
            self.mpv_process.stdin.write(b'p')
            self.mpv_process.stdin.flush()
            
            with self._lock:
                self.is_paused = True
            
            logger.info("Playback paused")
            return True
            
        except Exception as e:
            logger.error(f"Pause error: {e}")
            return False
    
    def resume(self) -> bool:
        """
        Resume playback.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.mpv_process or not self.is_playing or not self.is_paused:
                return False
            
            # Send pause command again to toggle (resume)
            self.mpv_process.stdin.write(b'p')
            self.mpv_process.stdin.flush()
            
            with self._lock:
                self.is_paused = False
            
            logger.info("Playback resumed")
            return True
            
        except Exception as e:
            logger.error(f"Resume error: {e}")
            return False
    
    def next_track(self) -> bool:
        """
        Skip to next track in queue.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if not self.track_queue:
                # No queue, search for related track
                if self.current_track:
                    query = f"{self.current_track['title']} similar songs"
                    threading.Thread(target=self.search_and_play, args=(query,), daemon=True).start()
                    return True
                return False
            
            if self.current_queue_index < len(self.track_queue) - 1:
                next_track = self.track_queue[self.current_queue_index + 1]
                threading.Thread(target=self._play_track, args=(next_track,), daemon=True).start()
                return True
            else:
                # At end of queue, search for related
                if self.current_track:
                    query = f"{self.current_track['title']} similar songs"
                    threading.Thread(target=self.search_and_play, args=(query,), daemon=True).start()
                    return True
                return False
    
    def previous_track(self) -> bool:
        """
        Go to previous track.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            # Try queue first
            if self.track_queue and self.current_queue_index > 0:
                prev_track = self.track_queue[self.current_queue_index - 1]
                threading.Thread(target=self._play_track, args=(prev_track,), daemon=True).start()
                return True
            
            # Fall back to history
            if len(self.track_history) >= 2:
                prev_track = self.track_history[-2]
                threading.Thread(target=self._play_track, args=(prev_track,), daemon=True).start()
                return True
            
            # Restart current track
            if self.current_track:
                threading.Thread(target=self._play_track, args=(self.current_track,), daemon=True).start()
                return True
            
            return False
    
    def stop(self) -> bool:
        """
        Stop playback and clear state.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._stop_monitoring()
            self._stop_mpv()
            
            with self._lock:
                self.current_track = None
                self.is_playing = False
                self.is_paused = False
                self.track_queue.clear()
                self.current_queue_index = -1
            
            logger.info("Playback stopped")
            return True
            
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        Get current playback status.
        
        Returns:
            Dictionary with status information
        """
        with self._lock:
            return {
                'is_playing': self.is_playing,
                'is_paused': self.is_paused,
                'current_track': self.current_track,
                'queue_length': len(self.track_queue),
                'queue_position': self.current_queue_index + 1 if self.current_queue_index >= 0 else 0,
                'history_length': len(self.track_history)
            }
    
    def add_to_queue(self, query: str) -> bool:
        """
        Add a track to the queue by search query.
        
        Args:
            query: Search query
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Search for the track
            search_cmd = [
                'yt-dlp',
                '--default-search', 'ytsearch1',
                '--skip-download',
                '--print', '%(id)s|%(title)s|%(uploader)s|%(duration)s',
                f'ytsearch1:{query}'
            ]
            
            result = subprocess.run(
                search_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return False
            
            output = result.stdout.strip()
            if not output:
                return False
            
            parts = output.split('|')
            if len(parts) < 4:
                return False
            
            video_id, title, uploader, duration = parts[0], parts[1], parts[2], parts[3]
            
            track = {
                'id': video_id,
                'title': title,
                'artist': uploader,
                'duration': duration,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'query': query
            }
            
            with self._lock:
                self.track_queue.append(track)
            
            logger.info(f"Added to queue: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Add to queue error: {e}")
            return False
    
    def _stop_mpv(self):
        """Stop the mpv process."""
        if self.mpv_process:
            try:
                self.mpv_process.terminate()
                self.mpv_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.mpv_process.kill()
            except Exception as e:
                logger.error(f"Error stopping mpv: {e}")
            finally:
                self.mpv_process = None
    
    def _start_monitor(self):
        """Start monitoring thread to detect when track ends."""
        self._stop_monitoring()
        
        self._should_stop_monitoring = False
        self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._monitor_thread.start()
    
    def _stop_monitoring(self):
        """Stop monitoring thread."""
        self._should_stop_monitoring = True
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
    
    def _monitor_playback(self):
        """Monitor playback and auto-play next track when current ends."""
        while not self._should_stop_monitoring:
            time.sleep(1)
            
            if self.mpv_process:
                poll_result = self.mpv_process.poll()
                
                if poll_result is not None:
                    # Process ended
                    logger.info("Track ended, playing next...")
                    
                    with self._lock:
                        self.is_playing = False
                        self.is_paused = False
                    
                    # Auto-play next track
                    self.next_track()
                    break
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        logger.info("Music player cleaned up")


# Global instance
_music_player: Optional[YouTubeMusicPlayer] = None


def get_music_player() -> YouTubeMusicPlayer:
    """Get or create the global YouTubeMusicPlayer instance."""
    global _music_player
    if _music_player is None:
        _music_player = YouTubeMusicPlayer()
    return _music_player
