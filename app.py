"""
Smart Frame - Main Flask Application
Central server managing system state and exposing REST APIs.
"""

import logging
import os
import yaml
from flask import Flask, jsonify, request, send_from_directory
import subprocess
import threading

# Import backend modules
from backend.state_manager import get_state_manager
from backend.message_manager import get_message_manager
from backend.music_controller import get_music_controller
from backend.music_player import get_music_player  # New lightweight music player
from backend.photo_manager import get_photo_manager
from backend import system_controls
from backend.git_updater import start_git_updater
from backend.scheduled_message_manager import start_scheduled_message_manager

# Import constants
from config.constants import STATE_IDLE, STATE_CLOCK, STATE_MUSIC


# Initialize Flask app
app = Flask(__name__, static_folder='ui', static_url_path='')
@app.route("/")
def root():
    return app.send_static_file("index.html")

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml')

def load_config():
    """Load configuration from settings.yaml"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {
            'clock_timeout': 120,
            'message_timeout': 300,
            'default_volume': 70,
            'default_brightness': 100,
        }

config = load_config()

# Initialize managers with config
state_manager = get_state_manager(config.get('clock_timeout', 120))
message_manager = get_message_manager(config.get('message_timeout', 300))
music_controller = get_music_controller()  # Legacy Chromium-based controller
music_player = get_music_player()  # New lightweight YouTube music player
photo_manager = get_photo_manager(config.get('photos_dir', '/home/raspberrypi4/projects/smart_frame/photos'))


# ============================================================================
# Static File Routes
# ============================================================================

@app.route('/')
def serve_index():
    """Serve the main UI page."""
    return send_from_directory('ui', 'index.html')


@app.route('/games/<path:filename>')
def serve_games(filename):
    """Serve game files from games directory."""
    return send_from_directory('games', filename)


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from ui directory."""
    return send_from_directory('ui', filename)


# ============================================================================
# State API Routes
# ============================================================================

@app.route('/state', methods=['GET'])
def get_state():
    """
    Get the current system state.
    
    Returns:
        JSON with current state and additional info
    """
    current_state = state_manager.get_state()
    response = {
        'state': current_state,
        'success': True,
    }
    
    # Add music info if in music state
    if current_state == STATE_MUSIC:
        response['artist'] = music_controller.get_current_artist()
    
    return jsonify(response)


@app.route('/tap', methods=['POST'])
def handle_tap():
    """
    Handle screen tap event.
    Cycles through states: IDLE -> CLOCK -> IDLE
    (Music state is only entered via voice/API)
    
    Returns:
        JSON with new state
    """
    current = state_manager.get_state()
    
    if current == STATE_IDLE:
        state_manager.set_state(STATE_CLOCK)
    elif current == STATE_CLOCK:
        state_manager.set_state(STATE_IDLE)
    elif current == STATE_MUSIC:
        # Tapping during music does nothing (must use stop command)
        pass
    
    return jsonify({
        'state': state_manager.get_state(),
        'success': True,
    })


# ============================================================================
# Message API Routes
# ============================================================================

@app.route('/message', methods=['POST'])
def set_message():
    """
    Set a new message.
    
    Request body:
        { "message": "Your message text" }
    
    Returns:
        JSON confirmation
    """
    data = request.get_json() or {}
    message = data.get('message', '')
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'Message is required',
        }), 400
    
    message_manager.set_message(message)
    
    return jsonify({
        'success': True,
        'message': message,
    })


@app.route('/message/active', methods=['GET'])
def get_active_message():
    """
    Get the currently active message.
    
    Returns:
        JSON with message or null
    """
    message = message_manager.get_active_message()
    
    return jsonify({
        'success': True,
        'message': message,
    })


@app.route('/message/clear', methods=['POST'])
def clear_message():
    """
    Clear the active message.
    
    Returns:
        JSON confirmation
    """
    message_manager.clear_message()
    
    return jsonify({
        'success': True,
    })


@app.route('/message/history', methods=['GET'])
def get_message_history():
    """
    Get the history of delivered scheduled messages.
    
    Returns:
        JSON array of delivered messages with timestamps
    """
    from backend.scheduled_message_manager import get_scheduled_message_manager
    manager = get_scheduled_message_manager()
    history = manager.get_message_history()
    
    return jsonify({
        'success': True,
        'messages': history,
        'count': len(history),
    })


# ============================================================================
# Music API Routes (New Lightweight Player)
# ============================================================================

@app.route('/api/music/search', methods=['POST'])
def music_search():
    """
    Search YouTube and play a song.
    
    Request body:
        { "query": "song name or artist" }
    
    Returns:
        JSON with track info and status
    """
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query is required',
        }), 400
    
    success = music_player.search_and_play(query)
    
    if success:
        state_manager.set_state(STATE_MUSIC)
        status = music_player.get_status()
        return jsonify({
            'success': True,
            'state': STATE_MUSIC,
            'status': status,
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to find or play track',
        }), 500


@app.route('/api/music/play', methods=['POST'])
def music_play():
    """
    Resume playback (unpause).
    
    Returns:
        JSON confirmation
    """
    success = music_player.resume()
    
    return jsonify({
        'success': success,
        'status': music_player.get_status(),
    })


@app.route('/api/music/pause', methods=['POST'])
def music_pause():
    """
    Pause playback.
    
    Returns:
        JSON confirmation
    """
    success = music_player.pause()
    
    return jsonify({
        'success': success,
        'status': music_player.get_status(),
    })


@app.route('/api/music/next', methods=['POST'])
def music_next():
    """
    Skip to next track.
    
    Returns:
        JSON confirmation
    """
    success = music_player.next_track()
    
    return jsonify({
        'success': success,
        'status': music_player.get_status(),
    })


@app.route('/api/music/previous', methods=['POST'])
def music_previous():
    """
    Go to previous track.
    
    Returns:
        JSON confirmation
    """
    success = music_player.previous_track()
    
    return jsonify({
        'success': success,
        'status': music_player.get_status(),
    })


@app.route('/api/music/stop', methods=['POST'])
def music_stop():
    """
    Stop playback completely.
    
    Returns:
        JSON confirmation
    """
    success = music_player.stop()
    
    if success:
        state_manager.set_state(STATE_IDLE)
        return jsonify({
            'success': True,
            'state': STATE_IDLE,
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to stop music',
        }), 500


@app.route('/api/music/status', methods=['GET'])
def music_status():
    """
    Get current playback status.
    
    Returns:
        JSON with current track info and playback state
    """
    status = music_player.get_status()
    
    return jsonify({
        'success': True,
        'status': status,
    })


@app.route('/api/music/queue/add', methods=['POST'])
def music_queue_add():
    """
    Add a track to the queue.
    
    Request body:
        { "query": "song name or artist" }
    
    Returns:
        JSON confirmation
    """
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query is required',
        }), 400
    
    success = music_player.add_to_queue(query)
    
    return jsonify({
        'success': success,
        'status': music_player.get_status(),
    })


# ============================================================================
# Legacy Music API Routes (Chromium-based - kept for compatibility)
# ============================================================================

@app.route('/music/play', methods=['POST'])
def play_music():
    """
    Start playing music (legacy endpoint - redirects to new player).
    
    Request body:
        { "artist": "Artist name" } (optional)
    
    Returns:
        JSON confirmation
    """
    data = request.get_json() or {}
    artist = data.get('artist', None)
    
    # Use new player instead
    if artist:
        success = music_player.search_and_play(artist)
    else:
        success = music_player.search_and_play("popular music")
    
    if success:
        state_manager.set_state(STATE_MUSIC)
        return jsonify({
            'success': True,
            'state': STATE_MUSIC,
            'artist': artist,
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to start music',
        }), 500


@app.route('/music/stop', methods=['POST'])
def stop_music():
    """
    Stop playing music (legacy endpoint).
    
    Returns:
        JSON confirmation
    """
    success = music_player.stop()
    
    if success:
        state_manager.set_state(STATE_IDLE)
        return jsonify({
            'success': True,
            'state': STATE_IDLE,
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to stop music',
        }), 500


# ============================================================================
# System Control API Routes
# ============================================================================

@app.route('/volume', methods=['POST'])
def set_volume():
    """
    Set system volume.
    
    Request body:
        { "level": 0-100 }
    
    Returns:
        JSON confirmation
    """
    data = request.get_json() or {}
    level = data.get('level')
    
    if level is None:
        return jsonify({
            'success': False,
            'error': 'Level is required',
        }), 400
    
    try:
        level = int(level)
        level = max(0, min(100, level))
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'error': 'Level must be a number',
        }), 400
    
    success = system_controls.set_volume(level)
    
    return jsonify({
        'success': success,
        'level': level,
    })


@app.route('/brightness', methods=['POST'])
def set_brightness():
    """
    Set display brightness.
    
    Request body:
        { "level": 0-100 }
    
    Returns:
        JSON confirmation
    """
    data = request.get_json() or {}
    level = data.get('level')
    
    if level is None:
        return jsonify({
            'success': False,
            'error': 'Level is required',
        }), 400
    
    try:
        level = int(level)
        level = max(0, min(100, level))
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'error': 'Level must be a number',
        }), 400
    
    success = system_controls.set_brightness(level)
    
    return jsonify({
        'success': success,
        'level': level,
    })


@app.route('/bluetooth', methods=['POST'])
def toggle_bluetooth():
    """
    Toggle Bluetooth on/off.
    
    Request body:
        { "enabled": true/false }
    
    Returns:
        JSON confirmation
    """
    data = request.get_json() or {}
    enabled = data.get('enabled', False)
    
    success = system_controls.set_bluetooth(enabled)
    
    return jsonify({
        'success': success,
        'enabled': enabled,
    })


# ============================================================================
# Photo Slideshow API Routes
# ============================================================================

@app.route('/api/photos/current', methods=['GET'])
def get_current_photo():
    """
    Get the current photo in the slideshow.
    
    Returns:
        JSON with current photo info
    """
    current_photo = photo_manager.get_current_photo()
    
    if current_photo is None:
        return jsonify({
            'success': False,
            'error': 'No photos available',
            'photo': None,
            'index': 0,
            'total': 0,
        })
    
    return jsonify({
        'success': True,
        'photo': current_photo,
        'index': photo_manager.current_index,
        'total': photo_manager.get_photo_count(),
    })


@app.route('/api/photos/next', methods=['POST'])
def advance_to_next_photo():
    """
    Advance to the next photo in the slideshow.
    
    Returns:
        JSON with next photo info
    """
    next_photo = photo_manager.get_next_photo()
    
    if next_photo is None:
        return jsonify({
            'success': False,
            'error': 'No photos available',
            'photo': None,
            'index': 0,
            'total': 0,
        })
    
    return jsonify({
        'success': True,
        'photo': next_photo,
        'index': photo_manager.current_index,
        'total': photo_manager.get_photo_count(),
    })


@app.route('/api/photos/previous', methods=['POST'])
def go_to_previous_photo():
    """
    Go back to the previous photo in the slideshow.
    
    Returns:
        JSON with previous photo info
    """
    prev_photo = photo_manager.get_previous_photo()
    
    if prev_photo is None:
        return jsonify({
            'success': False,
            'error': 'No photos available',
            'photo': None,
            'index': 0,
            'total': 0,
        })
    
    return jsonify({
        'success': True,
        'photo': prev_photo,
        'index': photo_manager.current_index,
        'total': photo_manager.get_photo_count(),
    })


@app.route('/photos/<path:filename>')
def serve_photo(filename):
    """
    Serve a photo file from the photos directory.
    
    Args:
        filename: Photo filename (relative to photos directory)
    
    Returns:
        Photo file
    """
    try:
        # Get the photos directory path
        photos_dir = photo_manager.photos_dir
        
        # Security: ensure the file exists and is within the photos directory
        photo_path = photo_manager.get_photo_path(filename)
        
        if not photo_path.exists() or not photo_path.is_file():
            return jsonify({
                'success': False,
                'error': 'Photo not found',
            }), 404
        
        # Send the file
        return send_from_directory(str(photos_dir), filename)
        
    except Exception as e:
        logging.error(f"Error serving photo {filename}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to serve photo',
        }), 500


@app.route('/api/photos/rescan', methods=['POST'])
def rescan_photos():
    """
    Rescan the photos directory to pick up new/removed photos.
    
    Returns:
        JSON with scan results
    """
    count = photo_manager.rescan()
    
    return jsonify({
        'success': True,
        'count': count,
    })


# ============================================================================
# Health Check
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'state': state_manager.get_state(),
    })


# ============================================================================
# Scheduled Message Callback
# ============================================================================

def on_scheduled_message(msg: dict):
    """
    Callback triggered when a scheduled message is due.
    
    This function is called by the ScheduledMessageManager when a message's
    scheduled time is reached. It integrates with the existing message system.
    
    Args:
        msg: Dictionary containing message data (id, text, from, schedule_at, timezone)
    """
    text = msg.get('text', '')
    sender = msg.get('from', 'Unknown')
    msg_id = msg.get('id', 'unknown')
    
    # Format message with sender
    formatted_message = f"From {sender}: {text}"
    
    # Set as active message using existing message manager
    message_manager.set_message(formatted_message)
    
    # Log the delivery
    logging.info(f"Scheduled message delivered: [{msg_id}] {formatted_message[:50]}...")
    
    # TODO: Play notification chime
    # TODO: Trigger UI popup overlay regardless of current screen


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Configure logging for git updater
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting Smart Frame server...")
    print(f"Clock timeout: {config.get('clock_timeout')}s")
    print(f"Message timeout: {config.get('message_timeout')}s")
    
    # Start background git updater (checks for updates every 10 minutes)
    start_git_updater()
    print("Git auto-updater started (interval: 10 minutes)")
    
    # Start scheduled message manager (checks every 30 seconds)
    start_scheduled_message_manager(on_message_callback=on_scheduled_message)
    print("Scheduled message manager started (interval: 30 seconds)")
    
    # Register cleanup handler for music player
    import atexit
    atexit.register(music_player.cleanup)
    
    # Run the Flask server
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
        )
    finally:
        # Cleanup on exit
        music_player.cleanup()
