"""
Git Auto-Updater Module
Periodically pulls updates from the remote repository in a background thread.
"""

import logging
import os
import subprocess
import threading
import time

# Configure logging for this module
logger = logging.getLogger(__name__)

# Update interval in seconds (2 minutes)
UPDATE_INTERVAL = 120


class GitUpdater:
    """
    Background git updater that periodically pulls from remote.
    
    Features:
    - Runs in a daemon thread (auto-stops when main app exits)
    - Never blocks the main Flask thread
    - Catches all errors and logs them
    - Detects and logs when new commits are pulled
    - Idempotent: no-op when repo is already up to date
    """
    
    def __init__(self, repo_path: str, interval: int = UPDATE_INTERVAL):
        """
        Initialize the updater.
        
        Args:
            repo_path: Absolute path to the git repository root
            interval: Seconds between update checks (default: 120)
        """
        self.repo_path = repo_path
        self.interval = interval
        self._thread = None
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the background updater thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("GitUpdater is already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.name = "GitUpdater"
        self._thread.start()
        logger.info(
            f"GitUpdater started. Checking for updates every {self.interval} seconds."
        )
    
    def stop(self):
        """Signal the updater to stop (for graceful shutdown if needed)."""
        self._stop_event.set()
        logger.info("GitUpdater stop signal sent")
    
    def _run_loop(self):
        """Main loop that runs in the background thread."""
        while not self._stop_event.is_set():
            try:
                self._do_update()
            except Exception as e:
                # Catch absolutely everything to prevent thread death
                logger.error(f"Unexpected error in GitUpdater loop: {e}")
            
            # Sleep in small increments to allow faster shutdown response
            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
    
    def _do_update(self):
        """
        Execute git pull and handle the result.
        
        This method catches all subprocess errors and logs them.
        It never raises exceptions to the caller.
        """
        logger.debug("Checking for git updates...")
        
        try:
            # Run git pull with timeout to prevent hanging
            result = subprocess.run(
                ["git", "pull", "--no-rebase"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
            )
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if result.returncode != 0:
                # Git command failed
                logger.error(f"git pull failed (exit {result.returncode}): {stderr}")
                return
            
            # Check if new commits were pulled
            if self._has_new_commits(stdout):
                logger.info(f"NEW COMMITS PULLED: {stdout}")
                self._on_new_commits(stdout)
            else:
                logger.debug(f"Repository up to date: {stdout}")
        
        except subprocess.TimeoutExpired:
            logger.error("git pull timed out after 60 seconds")
        except FileNotFoundError:
            logger.error("git command not found. Is git installed?")
        except Exception as e:
            logger.error(f"git pull error: {type(e).__name__}: {e}")
    
    def _has_new_commits(self, output: str) -> bool:
        """
        Determine if git pull fetched new commits.
        
        Args:
            output: stdout from git pull
        
        Returns:
            True if new commits were pulled, False otherwise
        """
        # "Already up to date." means no new commits
        # Any other output typically indicates changes were pulled
        normalized = output.lower().strip()
        return "already up to date" not in normalized and len(normalized) > 0
    
    def _on_new_commits(self, output: str):
        """
        Handle new commits being pulled.
        
        This is a hook for future functionality (e.g., signaling restart).
        Currently just logs the event.
        
        Args:
            output: stdout from git pull showing what was updated
        """
        # Internal signal: new commits detected
        # Future: could set a flag, emit an event, or trigger app reload
        logger.info("Signal: Repository updated with new commits")


# Module-level instance for convenience
_updater_instance = None


def start_git_updater(repo_path: str = None, interval: int = UPDATE_INTERVAL):
    """
    Start the global git updater instance.
    
    Args:
        repo_path: Path to repo root. Defaults to project root.
        interval: Seconds between checks. Defaults to 600 (10 minutes).
    
    Returns:
        The GitUpdater instance
    """
    global _updater_instance
    
    if repo_path is None:
        # Default to project root (parent of backend/)
        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    _updater_instance = GitUpdater(repo_path, interval)
    _updater_instance.start()
    return _updater_instance


def stop_git_updater():
    """Stop the global git updater instance."""
    global _updater_instance
    if _updater_instance is not None:
        _updater_instance.stop()
