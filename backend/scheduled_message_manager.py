"""
Scheduled Message Manager Module
Handles scheduled messages from a JSON file with background checking.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set

# Try to import zoneinfo (Python 3.9+), fall back to pytz pattern
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESSAGES_DIR = os.path.join(PROJECT_ROOT, 'messages')
SCHEDULED_MESSAGES_FILE = os.path.join(MESSAGES_DIR, 'scheduled_messages.json')
DELIVERED_IDS_FILE = os.path.join(MESSAGES_DIR, 'delivered_ids.json')
MESSAGE_HISTORY_FILE = os.path.join(MESSAGES_DIR, 'message_history.json')

# Check interval in seconds
CHECK_INTERVAL = 30


class ScheduledMessageManager:
    """
    Manages scheduled messages with background checking.
    
    Features:
    - Loads messages from scheduled_messages.json (authored via GitHub)
    - Checks every 30 seconds for due messages
    - Tracks delivered message IDs locally for idempotency
    - Handles timezone conversions
    - Delivers missed messages when device comes online
    - Never modifies the source file or pushes to GitHub
    """
    
    def __init__(self, on_message_callback: Optional[Callable[[Dict], None]] = None):
        """
        Initialize the scheduled message manager.
        
        Args:
            on_message_callback: Function to call when a message is due.
                                 Receives the full message dict.
        """
        self._on_message_callback = on_message_callback
        self._delivered_ids: Set[str] = set()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Ensure messages directory exists
        os.makedirs(MESSAGES_DIR, exist_ok=True)
        
        # Load previously delivered IDs from disk
        self._load_delivered_ids()
    
    def start(self):
        """Start the background checker thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("ScheduledMessageManager is already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.name = "ScheduledMessageChecker"
        self._thread.start()
        logger.info(
            f"ScheduledMessageManager started. Checking every {CHECK_INTERVAL} seconds."
        )
    
    def stop(self):
        """Signal the checker to stop."""
        self._stop_event.set()
        logger.info("ScheduledMessageManager stop signal sent")
    
    def set_callback(self, callback: Callable[[Dict], None]):
        """Set or update the message delivery callback."""
        self._on_message_callback = callback
    
    def get_delivered_ids(self) -> List[str]:
        """Get list of all delivered message IDs."""
        with self._lock:
            return list(self._delivered_ids)
    
    def get_message_history(self) -> List[Dict]:
        """Get the full message history with delivery timestamps."""
        try:
            if not os.path.exists(MESSAGE_HISTORY_FILE):
                return []
            with open(MESSAGE_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading message history: {e}")
            return []
    
    def _run_loop(self):
        """Main loop that runs in the background thread."""
        while not self._stop_event.is_set():
            try:
                self._check_scheduled_messages()
            except Exception as e:
                logger.error(f"Unexpected error in message checker loop: {e}")
            
            # Sleep in small increments for faster shutdown response
            for _ in range(CHECK_INTERVAL):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
    
    def _check_scheduled_messages(self):
        """Load scheduled messages and deliver any that are due."""
        messages = self._load_scheduled_messages()
        if not messages:
            return
        
        now = datetime.now(timezone.utc)
        
        for msg in messages:
            try:
                msg_id = msg.get('id')
                if not msg_id:
                    logger.warning("Skipping message with no ID")
                    continue
                
                # Skip already delivered messages
                with self._lock:
                    if msg_id in self._delivered_ids:
                        continue
                
                # Parse schedule time
                schedule_time = self._parse_schedule_time(msg)
                if schedule_time is None:
                    continue
                
                # Check if message is due
                if now >= schedule_time:
                    self._deliver_message(msg)
            
            except Exception as e:
                logger.error(f"Error processing message {msg.get('id', 'unknown')}: {e}")
    
    def _load_scheduled_messages(self) -> List[Dict]:
        """
        Load and parse scheduled_messages.json.
        
        Returns:
            List of message dictionaries, or empty list on error.
        """
        if not os.path.exists(SCHEDULED_MESSAGES_FILE):
            logger.debug("No scheduled_messages.json file found")
            return []
        
        try:
            with open(SCHEDULED_MESSAGES_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
            
            if not isinstance(data, list):
                logger.error("scheduled_messages.json must contain a JSON array")
                return []
            
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in scheduled_messages.json: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading scheduled_messages.json: {e}")
            return []
    
    def _parse_schedule_time(self, msg: Dict) -> Optional[datetime]:
        """
        Parse the schedule_at field with timezone handling.
        
        Args:
            msg: Message dictionary with schedule_at and optional timezone
        
        Returns:
            datetime in UTC, or None if parsing fails
        """
        schedule_str = msg.get('schedule_at')
        if not schedule_str:
            logger.warning(f"Message {msg.get('id')} has no schedule_at field")
            return None
        
        tz_str = msg.get('timezone')
        
        try:
            # Parse the datetime string
            dt = datetime.strptime(schedule_str, '%Y-%m-%d %H:%M')
            
            # Apply timezone
            if tz_str and ZoneInfo is not None:
                try:
                    tz = ZoneInfo(tz_str)
                    dt = dt.replace(tzinfo=tz)
                except Exception:
                    logger.warning(
                        f"Unknown timezone '{tz_str}' for message {msg.get('id')}, "
                        "using local time"
                    )
                    dt = dt.astimezone()
            else:
                # No timezone specified or ZoneInfo unavailable - use local
                dt = dt.astimezone()
            
            # Convert to UTC for comparison
            return dt.astimezone(timezone.utc)
        
        except ValueError as e:
            logger.error(
                f"Invalid schedule_at format for message {msg.get('id')}: {e}. "
                "Expected: YYYY-MM-DD HH:MM"
            )
            return None
    
    def _deliver_message(self, msg: Dict):
        """
        Deliver a message and mark it as delivered.
        
        Args:
            msg: The message dictionary to deliver
        """
        msg_id = msg.get('id')
        
        with self._lock:
            # Double-check not already delivered (race condition guard)
            if msg_id in self._delivered_ids:
                return
            
            # Mark as delivered BEFORE triggering callback
            self._delivered_ids.add(msg_id)
        
        # Persist delivered ID to disk immediately
        self._save_delivered_ids()
        
        # Store in message history
        self._store_message_history(msg)
        
        logger.info(f"Delivering scheduled message: {msg_id}")
        
        # Trigger callback if set
        if self._on_message_callback:
            try:
                self._on_message_callback(msg)
            except Exception as e:
                logger.error(f"Error in message callback for {msg_id}: {e}")
        else:
            logger.warning("No message callback set - message logged only")
    
    def _load_delivered_ids(self):
        """Load delivered message IDs from disk."""
        try:
            if os.path.exists(DELIVERED_IDS_FILE):
                with open(DELIVERED_IDS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._delivered_ids = set(data)
                        logger.info(f"Loaded {len(self._delivered_ids)} delivered message IDs")
        except Exception as e:
            logger.error(f"Error loading delivered IDs: {e}")
            self._delivered_ids = set()
    
    def _save_delivered_ids(self):
        """Persist delivered message IDs to disk."""
        try:
            with open(DELIVERED_IDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self._delivered_ids), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving delivered IDs: {e}")
    
    def _store_message_history(self, msg: Dict):
        """
        Store delivered message in history file with delivery timestamp.
        
        Args:
            msg: The delivered message
        """
        try:
            history = self.get_message_history()
            
            # Create history entry
            entry = {
                'id': msg.get('id'),
                'text': msg.get('text'),
                'from': msg.get('from'),
                'scheduled_at': msg.get('schedule_at'),
                'scheduled_timezone': msg.get('timezone'),
                'delivered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            history.append(entry)
            
            with open(MESSAGE_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error storing message history: {e}")


# Module-level instance
_scheduled_manager: Optional[ScheduledMessageManager] = None


def get_scheduled_message_manager(
    on_message_callback: Optional[Callable[[Dict], None]] = None
) -> ScheduledMessageManager:
    """
    Get or create the global ScheduledMessageManager instance.
    
    Args:
        on_message_callback: Optional callback for message delivery
    
    Returns:
        The singleton ScheduledMessageManager instance
    """
    global _scheduled_manager
    if _scheduled_manager is None:
        _scheduled_manager = ScheduledMessageManager(on_message_callback)
    elif on_message_callback is not None:
        _scheduled_manager.set_callback(on_message_callback)
    return _scheduled_manager


def start_scheduled_message_manager(
    on_message_callback: Optional[Callable[[Dict], None]] = None
) -> ScheduledMessageManager:
    """
    Convenience function to get and start the manager.
    
    Args:
        on_message_callback: Optional callback for message delivery
    
    Returns:
        The started ScheduledMessageManager instance
    """
    manager = get_scheduled_message_manager(on_message_callback)
    manager.start()
    return manager
