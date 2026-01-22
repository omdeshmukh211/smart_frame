"""
Actions Module
Executes intents by calling appropriate backend APIs.
"""

import requests
from typing import Optional
from datetime import datetime

from command_parser import Intent, IntentType
from responses import get_response, speak_response


# Backend API base URL
API_BASE_URL = "http://localhost:5000"


def execute_intent(intent: Intent) -> bool:
    """
    Execute an intent by calling the appropriate backend API.
    
    Args:
        intent: The intent to execute
        
    Returns:
        True if execution was successful
    """
    handlers = {
        IntentType.PLAY_MUSIC: _handle_play_music,
        IntentType.STOP_MUSIC: _handle_stop_music,
        IntentType.SAY_TIME: _handle_say_time,
        IntentType.SHOW_CLOCK: _handle_show_clock,
        IntentType.SET_VOLUME: _handle_set_volume,
        IntentType.SET_BRIGHTNESS: _handle_set_brightness,
        IntentType.GREETING: _handle_greeting,
        IntentType.REPLY_UNKNOWN: _handle_unknown,
    }
    
    handler = handlers.get(intent.type, _handle_unknown)
    
    try:
        return handler(intent)
    except Exception as e:
        print(f"Error executing intent: {e}")
        speak_response(get_response("error"))
        return False


def _handle_play_music(intent: Intent) -> bool:
    """Handle play music intent."""
    artist = intent.parameters.get('artist', '')
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/music/play",
            json={"artist": artist},
            timeout=10
        )
        
        if response.status_code == 200:
            speak_response(get_response("music_playing", artist=artist))
            return True
        else:
            speak_response(get_response("music_error"))
            return False
            
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        speak_response(get_response("connection_error"))
        return False


def _handle_stop_music(intent: Intent) -> bool:
    """Handle stop music intent."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/music/stop",
            timeout=10
        )
        
        if response.status_code == 200:
            speak_response(get_response("music_stopped"))
            return True
        else:
            speak_response(get_response("music_error"))
            return False
            
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        speak_response(get_response("connection_error"))
        return False


def _handle_say_time(intent: Intent) -> bool:
    """Handle say time intent."""
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    
    speak_response(get_response("time", time=time_str))
    return True


def _handle_show_clock(intent: Intent) -> bool:
    """Handle show clock intent."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/tap",
            timeout=10
        )
        
        if response.status_code == 200:
            speak_response(get_response("showing_clock"))
            return True
        else:
            return False
            
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return False


def _handle_set_volume(intent: Intent) -> bool:
    """Handle set volume intent."""
    level = intent.parameters.get('level', 50)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/volume",
            json={"level": level},
            timeout=10
        )
        
        if response.status_code == 200:
            speak_response(get_response("volume_set", level=level))
            return True
        else:
            speak_response(get_response("error"))
            return False
            
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        speak_response(get_response("connection_error"))
        return False


def _handle_set_brightness(intent: Intent) -> bool:
    """Handle set brightness intent."""
    level = intent.parameters.get('level', 100)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/brightness",
            json={"level": level},
            timeout=10
        )
        
        if response.status_code == 200:
            speak_response(get_response("brightness_set", level=level))
            return True
        else:
            speak_response(get_response("error"))
            return False
            
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        speak_response(get_response("connection_error"))
        return False


def _handle_greeting(intent: Intent) -> bool:
    """Handle greeting intent."""
    speak_response(get_response("greeting"))
    return True


def _handle_unknown(intent: Intent) -> bool:
    """Handle unknown intent."""
    speak_response(get_response("unknown"))
    return True
