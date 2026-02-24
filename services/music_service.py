"""
Music Service
Headless YouTube Music player using yt-dlp + mpv.
Runs in QThread to avoid blocking UI.
"""

import logging
import subprocess
import threading
from typing import Optional, Dict, List
from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from pathlib import Path

from models.app_state import AppState

logger = logging.getLogger(__name__)


class MusicService(QThread):
    """
    Music player service using yt-dlp for search and mpv for playback.
    
    Features:
    - Search YouTube and play audio only
    - Play/pause/resume controls
    - Next/previous track with queue
    - Volume control
    - No browser required (headless)
    """
    
    track_changed = pyqtSignal(dict)  # Emitted when track changes
    playback_state_changed = pyqtSignal(bool, bool)  # playing, paused
    
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        self.mpv_process: Optional[QProcess] = None
        self.current_track: Optional[Dict] = None
        self.track_queue: List[Dict] = []
        self.track_history: List[Dict] = []
        self.current_queue_index = -1
        self._running = False
        self._lock = threading.Lock()
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required tools are installed."""
        # Check yt-dlp
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                timeout=5
            )
            logger.info(f"yt-dlp found: {result.stdout.decode().strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
        
        # Check mpv
        try:
            result = subprocess.run(
                ['mpv', '--version'],
                capture_output=True,
                timeout=5
            )
            logger.info("mpv found")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("mpv not found. Install with: sudo apt-get install mpv (Linux)")
    
    def run(self):
        """Background thread main loop."""
        self._running = True
        logger.info("Music service started")
        
        # Keep thread alive to handle signals
        while self._running:
            self.msleep(100)
    
    def stop(self):
        """Stop the service and cleanup."""
        logger.info("Stopping music service...")
        self._running = False
        
        # Stop playback
        self._stop_playback()
        
        self.wait(2000)
    
    def search_and_play(self, query: str) -> bool:
        """
        Search YouTube and play the top result.
        
        Args:
            query: Search query (song name, artist, etc.)
            
        Returns:
            True if successful
        """
        def _search_thread():
            try:
                logger.info(f"Searching YouTube for: {query}")
                
                # Use yt-dlp to search and get video URL
                search_cmd = [
                    'yt-dlp',
                    '--default-search', 'ytsearch1:',
                    '--skip-download',
                    '--get-id',
                    '--get-title',
                    '--get-uploader',
                    '--get-duration',
                    query
                ]
                
                result = subprocess.run(
                    search_cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode != 0:
                    logger.error(f"Search failed: {result.stderr}")
                    return
                
                # Parse result (format: title\nuploader\nduration\nvideo_id)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    title = lines[0]
                    video_id = lines[-1]  # Last line is video ID
                    
                    # Build track info
                    track_info = {
                        'title': title,
                        'artist': lines[1] if len(lines) > 2 else 'Unknown',
                        'video_id': video_id,
                        'url': f'https://www.youtube.com/watch?v={video_id}'
                    }
                    
                    # Play this track
                    self._play_track(track_info)
                    
                    # Add to queue
                    with self._lock:
                        self.track_queue.append(track_info)
                        self.current_queue_index = len(self.track_queue) - 1
                
            except subprocess.TimeoutExpired:
                logger.error("Search timeout")
            except Exception as e:
                logger.error(f"Search error: {e}")
        
        # Run search in background thread
        thread = threading.Thread(target=_search_thread, daemon=True)
        thread.start()
        return True
    
    def _play_track(self, track: Dict):
        """
        Play a track using mpv.
        
        Args:
            track: Track info dict with 'url' and metadata
        """
        try:
            # Stop current playback
            self._stop_playback()
            
            # Update state
            self.current_track = track
            self.app_state.set_current_track(track)
            self.track_changed.emit(track)
            
            logger.info(f"Playing: {track.get('title', 'Unknown')}")
            
            # Start mpv with yt-dlp integration
            # mpv will use yt-dlp automatically to extract audio stream
            self.mpv_process = QProcess()
            
            # mpv arguments for audio-only playback
            volume = self.app_state.get_setting('volume', 70)
            args = [
                '--no-video',  # Audio only
                '--volume=' + str(volume),
                '--ytdl-format=bestaudio',  # Best audio quality
                '--no-terminal',  # No terminal output
                track['url']
            ]
            
            self.mpv_process.finished.connect(self._on_playback_finished)
            self.mpv_process.start('mpv', args)
            
            # Update state
            self.app_state.set_music_playing(True)
            self.app_state.set_music_paused(False)
            self.playback_state_changed.emit(True, False)
            
        except Exception as e:
            logger.error(f"Error playing track: {e}")
            self.app_state.set_music_playing(False)
    
    def _stop_playback(self):
        """Stop current playback."""
        if self.mpv_process and self.mpv_process.state() == QProcess.Running:
            self.mpv_process.kill()
            self.mpv_process.waitForFinished(1000)
            self.mpv_process = None
        
        self.app_state.set_music_playing(False)
        self.app_state.set_music_paused(False)
        self.playback_state_changed.emit(False, False)
    
    def _on_playback_finished(self, exit_code, exit_status):
        """Called when mpv process finishes."""
        logger.info(f"Playback finished (exit code: {exit_code})")
        
        # Auto-play next track if available in queue
        with self._lock:
            has_next_in_queue = self.track_queue and self.current_queue_index < len(self.track_queue) - 1
        
        if self._running:
            if has_next_in_queue:
                # Play next from queue
                self.next()
            else:
                # Get and play recommended track
                self._autoplay_recommended()
    
    def pause(self):
        """Pause playback."""
        if self.mpv_process and self.mpv_process.state() == QProcess.Running:
            # Send pause command via stdin (mpv IPC)
            # For simplicity, we'll use kill/resume approach
            # In production, use mpv's IPC socket for proper control
            logger.info("Pause requested (stopping playback)")
            self._stop_playback()
            self.app_state.set_music_paused(True)
            self.playback_state_changed.emit(False, True)
    
    def resume(self):
        """Resume playback."""
        # Re-play current track
        if self.current_track:
            logger.info("Resuming playback")
            self._play_track(self.current_track)
    
    def next(self):
        """Play next track in queue."""
        with self._lock:
            if not self.track_queue:
                logger.info("No tracks in queue")
                return
            
            self.current_queue_index = (self.current_queue_index + 1) % len(self.track_queue)
            next_track = self.track_queue[self.current_queue_index]
        
        self._play_track(next_track)
    
    def previous(self):
        """Play previous track in queue."""
        with self._lock:
            if not self.track_queue:
                logger.info("No tracks in queue")
                return
            
            self.current_queue_index = (self.current_queue_index - 1) % len(self.track_queue)
            prev_track = self.track_queue[self.current_queue_index]
        
        self._play_track(prev_track)
    
    def set_volume(self, volume: int):
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0-100)
        """
        # For currently playing track, would need mpv IPC
        # For next track, it will use updated setting
        self.app_state.set_setting('volume', volume)
        logger.info(f"Volume set to {volume}%")
    
    def _get_recommended_track(self, current_video_id: str) -> Optional[Dict]:
        """
        Get a recommended track based on current video.
        
        Args:
            current_video_id: YouTube video ID of current track
            
        Returns:
            Track dict with title, artist, video_id, url or None if failed
        """
        try:
            logger.info(f"Fetching recommended tracks for video: {current_video_id}")
            
            # Use yt-dlp to get related videos
            # The --flat-playlist option with a playlist URL will give us related videos
            cmd = [
                'yt-dlp',
                '--flat-playlist',
                '--skip-download',
                '--print', '%(id)s|%(title)s|%(uploader)s',
                f'https://www.youtube.com/watch?v={current_video_id}&list=RD{current_video_id}',
                '--playlist-items', '2'  # Get the 2nd item (1st is current video)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                logger.warning(f"Could not fetch recommendations: {result.stderr}")
                # Fallback: search for similar songs
                return self._search_similar_track()
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 1:
                logger.warning("No recommended tracks found")
                return self._search_similar_track()
            
            # Parse the recommended track (format: video_id|title|uploader)
            parts = lines[0].split('|')
            if len(parts) >= 3:
                video_id, title, uploader = parts[0], parts[1], parts[2]
                
                return {
                    'title': title,
                    'artist': uploader,
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                }
            
            return self._search_similar_track()
            
        except subprocess.TimeoutExpired:
            logger.warning("Recommendation fetch timed out")
            return self._search_similar_track()
        except Exception as e:
            logger.error(f"Error fetching recommended track: {e}")
            return self._search_similar_track()
    
    def _search_similar_track(self) -> Optional[Dict]:
        """
        Search for a similar track when recommendations fail.
        
        Returns:
            Track dict or None
        """
        try:
            if not self.current_track:
                return None
            
            # Search for similar songs based on current track
            search_query = f"{self.current_track.get('title', '')} similar songs"
            logger.info(f"Searching for similar track: {search_query}")
            
            cmd = [
                'yt-dlp',
                '--default-search', 'ytsearch1:',
                '--skip-download',
                '--get-id',
                '--get-title',
                '--get-uploader',
                search_query
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                title = lines[0]
                video_id = lines[-1]
                
                return {
                    'title': title,
                    'artist': lines[1] if len(lines) > 2 else 'Unknown',
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for similar track: {e}")
            return None
    
    def _autoplay_recommended(self):
        """
        Fetch and play a recommended track in background thread.
        """
        def _fetch_and_play():
            try:
                # Get current track's video ID
                video_id = None
                with self._lock:
                    if self.current_track and 'video_id' in self.current_track:
                        video_id = self.current_track['video_id']
                
                if not video_id:
                    logger.warning("No video ID available for recommendations")
                    return
                
                # Get recommended track
                recommended = self._get_recommended_track(video_id)
                
                if recommended:
                    logger.info(f"Autoplaying recommended: {recommended['title']}")
                    
                    # Add to queue and play
                    with self._lock:
                        self.track_queue.append(recommended)
                        self.current_queue_index = len(self.track_queue) - 1
                    
                    self._play_track(recommended)
                else:
                    logger.warning("No recommended track found")
            
            except Exception as e:
                logger.error(f"Error in autoplay: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=_fetch_and_play, daemon=True)
        thread.start()
