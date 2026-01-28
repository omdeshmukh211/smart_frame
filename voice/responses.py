def speak_response(text):
    # Stub for TTS. Replace with local TTS engine if available (e.g., espeak, pyttsx3)
    print(f'[TTS] {text}')
    # Greetings
    "greeting": "Hello, I'm awake.",
    "goodbye": "Goodbye!",
    
    # Unknown/Error
    "unknown": "Sorry, I didn't understand that.",
    "error": "Sorry, something went wrong.",
    "connection_error": "Sorry, I couldn't connect to the system.",
    
    # Time
    "time": "The time is {time}.",
    
    # Clock
    "showing_clock": "Here's the clock.",
    
    # Music
    "music_playing": "Playing {artist}.",
    "music_stopped": "Music stopped.",
    "music_error": "Sorry, I couldn't play the music.",
    
    # Volume
    "volume_set": "Volume set to {level} percent.",
    "volume_up": "Volume increased.",
    "volume_down": "Volume decreased.",
    
    # Brightness
    "brightness_set": "Brightness set to {level} percent.",
    
    # Messages
    "message_received": "You have a new message.",
    "no_messages": "No new messages.",
}


def get_response(key: str, **kwargs) -> str:
    """
    Get a response string by key, with optional parameter substitution.
    
    Args:
        key: The response key
        **kwargs: Parameters to substitute into the response
        
    Returns:
        The formatted response string
    """
    template = RESPONSES.get(key, RESPONSES["unknown"])
    
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def speak_response(text: str) -> bool:
    """
    Speak a response using text-to-speech.
    
    Args:
        text: The text to speak
        
    Returns:
        True if speech was successful
    """
    print(f"[SPEAK] {text}")
    
    if not TTS_AVAILABLE:
        return False
    
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume (0-1)
        
        engine.say(text)
        engine.runAndWait()
        
        return True
    except Exception as e:
        print(f"Text-to-speech error: {e}")
        return False


def add_response(key: str, text: str) -> None:
    """
    Add or update a response template.
    
    Args:
        key: The response key
        text: The response template text
    """
    RESPONSES[key] = text


def list_responses() -> dict:
    """
    Get all available response templates.
    
    Returns:
        Dictionary of all responses
    """
    return RESPONSES.copy()
