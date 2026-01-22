"""
Command Parser Module
Maps recognized text to structured intents.
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Enum of all recognized intent types."""
    PLAY_MUSIC = "PLAY_MUSIC"
    STOP_MUSIC = "STOP_MUSIC"
    SAY_TIME = "SAY_TIME"
    SHOW_CLOCK = "SHOW_CLOCK"
    SET_VOLUME = "SET_VOLUME"
    SET_BRIGHTNESS = "SET_BRIGHTNESS"
    GREETING = "GREETING"
    REPLY_UNKNOWN = "REPLY_UNKNOWN"


@dataclass
class Intent:
    """Represents a parsed intent with optional parameters."""
    type: IntentType
    parameters: Dict[str, Any]
    raw_text: str
    confidence: float = 1.0


# Pattern definitions for intent matching
PATTERNS = {
    IntentType.PLAY_MUSIC: [
        r"play\s+(.+)",
        r"put on\s+(.+)",
        r"listen to\s+(.+)",
        r"play some\s+(.+)",
        r"start playing\s+(.+)",
    ],
    IntentType.STOP_MUSIC: [
        r"stop(?:\s+the)?\s*music",
        r"pause(?:\s+the)?\s*music",
        r"stop playing",
        r"turn off(?:\s+the)?\s*music",
    ],
    IntentType.SAY_TIME: [
        r"what(?:'s|\s+is)?\s*(?:the)?\s*time",
        r"tell me the time",
        r"what time is it",
        r"current time",
    ],
    IntentType.SHOW_CLOCK: [
        r"show(?:\s+the)?\s*clock",
        r"display(?:\s+the)?\s*clock",
        r"clock mode",
    ],
    IntentType.SET_VOLUME: [
        r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)",
        r"volume\s+(\d+)",
        r"set\s+volume\s+(\d+)",
    ],
    IntentType.SET_BRIGHTNESS: [
        r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)",
        r"brightness\s+(\d+)",
        r"set\s+brightness\s+(\d+)",
    ],
    IntentType.GREETING: [
        r"^(?:hey|hi|hello|good\s+(?:morning|afternoon|evening))(?:\s+smart\s*frame)?",
        r"wake up",
        r"are you (?:there|awake)",
    ],
}


def parse_command(text: str) -> Intent:
    """
    Parse a text command into a structured intent.
    
    Args:
        text: The recognized speech text
        
    Returns:
        Intent object with type and parameters
    """
    text_lower = text.lower().strip()
    
    # Try to match against each intent pattern
    for intent_type, patterns in PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                parameters = _extract_parameters(intent_type, match)
                return Intent(
                    type=intent_type,
                    parameters=parameters,
                    raw_text=text
                )
    
    # No pattern matched - return unknown intent
    return Intent(
        type=IntentType.REPLY_UNKNOWN,
        parameters={},
        raw_text=text,
        confidence=0.0
    )


def _extract_parameters(intent_type: IntentType, match: re.Match) -> Dict[str, Any]:
    """
    Extract parameters from a regex match based on intent type.
    
    Args:
        intent_type: The matched intent type
        match: The regex match object
        
    Returns:
        Dictionary of extracted parameters
    """
    parameters = {}
    
    if intent_type == IntentType.PLAY_MUSIC:
        if match.groups():
            parameters['artist'] = match.group(1).strip()
    
    elif intent_type == IntentType.SET_VOLUME:
        if match.groups():
            try:
                parameters['level'] = int(match.group(1))
            except ValueError:
                parameters['level'] = 50
    
    elif intent_type == IntentType.SET_BRIGHTNESS:
        if match.groups():
            try:
                parameters['level'] = int(match.group(1))
            except ValueError:
                parameters['level'] = 100
    
    return parameters


def get_intent_description(intent: Intent) -> str:
    """
    Get a human-readable description of an intent.
    
    Args:
        intent: The intent to describe
        
    Returns:
        Human-readable description string
    """
    descriptions = {
        IntentType.PLAY_MUSIC: lambda p: f"Play music: {p.get('artist', 'unknown')}",
        IntentType.STOP_MUSIC: lambda p: "Stop music",
        IntentType.SAY_TIME: lambda p: "Say the current time",
        IntentType.SHOW_CLOCK: lambda p: "Show clock display",
        IntentType.SET_VOLUME: lambda p: f"Set volume to {p.get('level', '?')}%",
        IntentType.SET_BRIGHTNESS: lambda p: f"Set brightness to {p.get('level', '?')}%",
        IntentType.GREETING: lambda p: "Greeting response",
        IntentType.REPLY_UNKNOWN: lambda p: "Unknown command",
    }
    
    desc_func = descriptions.get(intent.type, lambda p: "Unknown")
    return desc_func(intent.parameters)
