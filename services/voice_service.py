"""
Voice Service - Retro Hardware Style
Handles wake phrase detection, speech recognition, and command execution.
"""

import logging
import json
import threading
from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition not installed. Voice features disabled.")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed. TTS disabled.")


class VoiceService(QObject):
    """
    Voice command service with wake phrase detection.
    
    Signals:
        wake_detected: Emitted when wake phrase is detected
        transcription_ready: Emitted with transcribed text
        command_executed: Emitted when command is executed
    """
    
    wake_detected = pyqtSignal()
    transcription_ready = pyqtSignal(str)  # Transcribed text
    command_executed = pyqtSignal(str, bool)  # Command, success
    
    def __init__(self, app_state, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        
        self.is_listening = False
        self.wake_phrases = []
        self.command_map = {}
        
        self._recognizer = None
        self._microphone = None
        self._listen_thread = None
        
        self._load_config()
        self._init_speech()
    
    def _load_config(self):
        """Load wake phrases and commands from config files."""
        try:
            # Load wake phrases
            with open('config/voice_triggers.json', 'r') as f:
                data = json.load(f)
                self.wake_phrases = [p.strip().lower() for p in data.get('wake_phrases', [])]
            
            # Load command map
            with open('config/voice_commands.json', 'r') as f:
                self.command_map = json.load(f)
            
            logger.info(f"Loaded {len(self.wake_phrases)} wake phrases, {len(self.command_map)} commands")
        except Exception as e:
            logger.error(f"Error loading voice config: {e}")
    
    def _init_speech(self):
        """Initialize speech recognition."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return
        
        try:
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            logger.info("Speech recognition initialized")
        except Exception as e:
            logger.error(f"Error initializing speech recognition: {e}")
    
    def start_listening(self):
        """Start listening for wake phrases."""
        if not SPEECH_RECOGNITION_AVAILABLE or not self._microphone:
            logger.warning("Speech recognition not available")
            return False
        
        if self.is_listening:
            return True
        
        self.is_listening = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        
        logger.info("Voice service started")
        return True
    
    def stop_listening(self):
        """Stop listening for wake phrases."""
        self.is_listening = False
        logger.info("Voice service stopped")
    
    def _listen_loop(self):
        """Background thread that listens for wake phrases."""
        while self.is_listening:
            try:
                with self._microphone as source:
                    # Listen for audio
                    audio = self._recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Recognize speech
                text = self._recognizer.recognize_google(audio).lower()
                logger.info(f"Heard: {text}")
                
                # Check for wake phrase
                for wake_phrase in self.wake_phrases:
                    if text.startswith(wake_phrase):
                        # Wake phrase detected!
                        self.wake_detected.emit()
                        
                        # Extract command (text after wake phrase)
                        command_text = text[len(wake_phrase):].strip()
                        
                        if command_text:
                            self.transcription_ready.emit(command_text)
                            self._process_command(command_text)
                        else:
                            # Just wake phrase, wait for command
                            self._listen_for_command()
                        
                        break
            
            except sr.WaitTimeoutError:
                # No speech detected, continue listening
                continue
            except sr.UnknownValueError:
                # Speech not understood
                continue
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                continue
    
    def _listen_for_command(self):
        """Listen for a command after wake phrase."""
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self._recognizer.recognize_google(audio).lower()
            logger.info(f"Command: {text}")
            
            self.transcription_ready.emit(text)
            self._process_command(text)
        
        except Exception as e:
            logger.error(f"Error listening for command: {e}")
            self._speak("I didn't catch that")
    
    def _process_command(self, text: str):
        """Process a voice command."""
        text = text.lower().strip()
        
        # Direct match
        if text in self.command_map:
            action = self.command_map[text]
            success = self._execute_action(action, text)
            self.command_executed.emit(text, success)
            return
        
        # Fuzzy match - check if any command key is in the text
        for key, action in self.command_map.items():
            if key in text:
                success = self._execute_action(action, text)
                self.command_executed.emit(text, success)
                return
        
        # No match
        logger.info(f"No command match for: {text}")
        self._speak("I don't understand that command")
        self.command_executed.emit(text, False)
    
    def _execute_action(self, action: str, text: str) -> bool:
        """Execute a voice action."""
        logger.info(f"Executing action: {action}")
        
        from models.app_state import AppState
        
        # Game launching - specific games
        if action == "launch_snake":
            self.navigate(AppState.VIEW_GAMES)
            self._speak("Opening Snake game")
            # TODO: Auto-launch specific game
            return True
        
        if action == "launch_tictactoe":
            self.navigate(AppState.VIEW_GAMES)
            self._speak("Opening Tic Tac Toe")
            return True
        
        if action == "launch_wordle":
            self.navigate(AppState.VIEW_GAMES)
            self._speak("Opening Wordle")
            return True
        
        # Games menu
        if action == "open_games" or "game" in action.lower():
            self.navigate(AppState.VIEW_GAMES)
            self._speak("Opening games")
            return True
        
        # Music commands
        if action == "open_music" or "music" in action.lower():
            self.navigate(AppState.VIEW_MUSIC)
            self._speak("Opening music player")
            return True
        
        if action == "stop_music":
            # TODO: Send stop command to music service
            self._speak("Stopping music")
            return True
        
        # Messages
        if action == "open_messages" or "message" in action.lower():
            self.navigate(AppState.VIEW_MESSAGES)
            self._speak("Opening messages")
            return True
        
        # Time
        if action == "speak_time" or "time" in action.lower():
            from datetime import datetime
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            self._speak(f"The time is {time_str}")
            return True
        
        # Idle/sleep
        if action == "enter_idle" or "idle" in action.lower() or "sleep" in action.lower():
            self.navigate(AppState.VIEW_IDLE)
            self._speak("Going to sleep")
            return True
        
        # Settings
        if action == "open_settings" or "setting" in action.lower():
            self.navigate(AppState.VIEW_SETTINGS)
            self._speak("Opening settings")
            return True
        
        # Home
        if action == "go_home" or action == "home_screen":
            self.navigate(AppState.VIEW_HOME)
            self._speak("Going home")
            return True
        
        # Unknown action
        logger.warning(f"Unknown action: {action}")
        return False
    
    def _speak(self, text: str):
        """Speak text using TTS."""
        if not TTS_AVAILABLE:
            logger.info(f"[SPEAK] {text}")
            return
        
        try:
            def speak_async():
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 0.9)
                engine.say(text)
                engine.runAndWait()
            
            # Run TTS in background thread to not block
            threading.Thread(target=speak_async, daemon=True).start()
        except Exception as e:
            logger.error(f"TTS error: {e}")
