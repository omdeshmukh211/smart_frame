"""
Voice Listener Module
Captures speech and converts to text.
Sends recognized text to command_parser for processing.
"""

import time
from typing import Optional, Callable

# Note: Requires speech_recognition package
# pip install SpeechRecognition pyaudio

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: speech_recognition not installed. Voice features disabled.")


class VoiceListener:
    """Listens for voice input and converts speech to text."""
    
    def __init__(self):
        self._recognizer: Optional[object] = None
        self._microphone: Optional[object] = None
        self._is_listening: bool = False
        self._on_text_callback: Optional[Callable[[str], None]] = None
        
        if SPEECH_RECOGNITION_AVAILABLE:
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            
            # Adjust for ambient noise on startup
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
    
    def set_text_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback to be called when speech is recognized.
        
        Args:
            callback: Function that receives recognized text
        """
        self._on_text_callback = callback
    
    def listen_once(self) -> Optional[str]:
        """
        Listen for a single phrase and return the recognized text.
        
        Returns:
            Recognized text or None if recognition failed
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("Speech recognition not available")
            return None
        
        try:
            with self._microphone as source:
                print("Listening...")
                audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Use Google's speech recognition
            text = self._recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("Listening timed out")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Recognition service error: {e}")
            return None
        except Exception as e:
            print(f"Error during recognition: {e}")
            return None
    
    def start_continuous_listening(self) -> None:
        """Start listening continuously for voice commands."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("Speech recognition not available")
            return
        
        self._is_listening = True
        print("Starting continuous listening...")
        
        while self._is_listening:
            text = self.listen_once()
            
            if text and self._on_text_callback:
                self._on_text_callback(text)
            
            # Small delay between listening attempts
            time.sleep(0.5)
    
    def stop_listening(self) -> None:
        """Stop continuous listening."""
        self._is_listening = False
        print("Stopped listening")
    
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening


# Global instance
_voice_listener: Optional[VoiceListener] = None


def get_voice_listener() -> VoiceListener:
    """Get or create the global VoiceListener instance."""
    global _voice_listener
    if _voice_listener is None:
        _voice_listener = VoiceListener()
    return _voice_listener


def main():
    """Main entry point for voice listener service."""
    from command_parser import parse_command
    from actions import execute_intent
    
    listener = get_voice_listener()
    
    def on_text_received(text: str):
        """Handle recognized text."""
        intent = parse_command(text)
        execute_intent(intent)
    
    listener.set_text_callback(on_text_received)
    
    try:
        listener.start_continuous_listening()
    except KeyboardInterrupt:
        listener.stop_listening()
        print("Voice listener stopped")


if __name__ == "__main__":
    main()
