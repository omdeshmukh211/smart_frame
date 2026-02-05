# Smart Frame

A retro hardware-style smart display built with **PyQt5**. Features voice control, photo slideshow, music player, games, and message system - all with a nostalgic monospace aesthetic.

---

## ✨ Features

### 🎮 Retro Hardware UI
- Pure black backgrounds with monospace Courier New fonts
- Discrete state changes (no animations)
- 40%-60% split home screen (clock left, photos right)
- Fixed 1024x600 resolution optimized for Raspberry Pi displays

### 📸 Photo Slideshow
- Edge-to-edge photo display
- 10-minute auto-advance or tap to change
- Scans local photo directory automatically
- Smooth QPixmap rendering

### 🎵 Music Player
- Headless YouTube Music via mpv (no browser required)
- Transport controls (play, pause, skip)
- Volume visualization bars
- Dancing bars visualizer

### 🎮 Built-in Games
- **Snake** - Classic grid-based game (20x20 grid)
- **Tic-Tac-Toe** - AI opponent with minimax strategy
- **Wordle** - Daily word puzzle with on-screen keyboard
- All games use native PyQt5 rendering with QPainter

### 🗣️ Voice Control
- Wake phrase detection ("hey om", "hello om")
- 30+ voice commands for navigation and control
- On-screen transcription display
- Text-to-speech feedback ("I'm listening")
- Completely offline using speech_recognition + pyttsx3

### 💬 Message System
- Scheduled messages with priority levels
- Full-screen blocking overlays
- Message history tracking
- Sound notification support

### 🌙 Day/Night Mode
- Automatic sun/moon icons (6am-6pm day mode)
- Larger icons (40px radius) in top-left
- Subtle visual adaptation

---

## 📦 Installation

### Prerequisites
- Raspberry Pi (tested on Pi 4) or Linux system
- Python 3.8+
- Display (1024x600 recommended)

### Quick Install

```bash
cd smart_frame
chmod +x install.sh
./install.sh
```

This will install:
- System dependencies (PyQt5, multimedia packages)
- Python packages (see requirements.txt)
- mpv for music playback
- Optional: TTS and speech recognition libraries

### Manual Installation

```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtmultimedia \
    mpv ffmpeg python3-pip

# Install Python packages
pip3 install -r requirements.txt

# Optional: Voice control dependencies
pip3 install SpeechRecognition pyttsx3 pyaudio
```

---

## 🚀 Usage

### Start the Application

```bash
# Standard mode (windowed)
python3 main.py

# Fullscreen mode
python3 main.py --fullscreen

# Run via start script
chmod +x start.sh
./start.sh
```

### Systemd Service (Auto-start on boot)

```bash
# Copy service file
sudo cp services/smart_frame_native.service /etc/systemd/system/

# Enable and start
sudo systemctl enable smart_frame_native
sudo systemctl start smart_frame_native

# Check status
sudo systemctl status smart_frame_native
```

---

## 🎯 Navigation

### Screen Flow
```
IDLE (robot face) 
  ↓ tap
HOME (clock + photos)
  ↓ tap Menu button
MENU
  ↓ select option
├── Games (Snake, Tic-Tac-Toe, Wordle)
├── Music (YouTube Music player)
├── Messages (Message history)
└── Settings (Volume, brightness, WiFi)
```

### Controls
- **Tap** - Navigate forward
- **Escape/Back** - Navigate backward
- **Mic button** - Toggle voice control
- **Menu button** - Access main menu (bottom-right on home screen)

---

## 🗣️ Voice Commands

### Activation
1. Tap mic icon (top-right on home screen) - turns green
2. Say wake phrase: **"hey om"** or **"hello om"**
3. System responds: "I'm listening"
4. Speak your command
5. Transcription appears at bottom of screen
6. Command executes with voice feedback

### Available Commands

**Navigation:**
- "open games" / "show games"
- "play music" / "open music"
- "show messages" / "check messages"
- "open settings"
- "go home"
- "go to sleep"

**Games:**
- "play snake" / "open snake"
- "play tic tac toe" / "play x o"
- "play wordle" / "open wordle"

**Utilities:**
- "what time is it" / "tell me the time"
- "stop music" / "pause music"

---

## ⚙️ Configuration

### Settings File: `config/settings.yaml`

```yaml
# Photo slideshow
photo_directory: "/home/pi/Pictures"
slideshow_interval: 600  # 10 minutes in seconds

# Music
music_volume: 75
music_backend: "mpv"  # Uses mpv for headless playback

# Display
fullscreen: true
resolution:
  width: 1024
  height: 600

# Voice
voice_enabled: true
wake_phrases:
  - "hey om"
  - "hello om"
```

### Voice Commands: `config/voice_commands.json`

Add or modify voice commands by editing the JSON mappings:

```json
{
  "your custom phrase": "action_name",
  "play my playlist": "open_music"
}
```

---

## 📂 Project Structure

```
smart_frame/
├── main.py                     # Application entry point
├── install.sh                  # Installation script
├── start.sh                    # Launch script
├── requirements.txt            # Python dependencies
│
├── backend/                    # Backend services
│   ├── music_controller.py     # Music playback control
│   ├── photo_manager.py        # Photo directory scanner
│   ├── message_manager.py      # Message handling
│   └── system_controls.py      # System utilities
│
├── ui/                         # PyQt5 User Interface
│   ├── main_window.py          # Main window & navigation
│   ├── views/                  # Screen views
│   │   ├── idle_view.py        # Robot face idle screen
│   │   ├── home_view.py        # Clock + photos home screen
│   │   ├── menu_view.py        # Text menu navigation
│   │   ├── games_view.py       # Games launcher
│   │   ├── music_view.py       # Music player UI
│   │   ├── messages_view.py    # Message list/detail
│   │   └── settings_view.py    # Settings UI
│   ├── games/                  # Native game widgets
│   │   ├── snake_game.py       # Snake game
│   │   ├── tictactoe_game.py   # Tic-Tac-Toe game
│   │   └── wordle_game.py      # Wordle game
│   └── widgets/
│       └── message_overlay.py  # Full-screen message display
│
├── services/                   # Background services
│   ├── photo_service.py        # Photo slideshow service
│   ├── music_service.py        # Music player service
│   └── voice_service.py        # Voice recognition service
│
├── models/                     # Data models
│   └── app_state.py           # Application state manager
│
├── config/                     # Configuration
│   ├── settings.yaml          # App settings
│   ├── settings_loader.py     # Config loader
│   ├── voice_commands.json    # Voice command mappings
│   └── voice_triggers.json    # Wake phrases
│
├── voice/                      # Voice processing
│   ├── command_parser.py      # Command parsing utilities
│   ├── actions.py             # Action handlers
│   └── responses.py           # TTS responses
│
├── data/                       # Runtime data
│   ├── logs.txt               # Application logs
│   └── messages.txt           # Message storage
│
├── messages/                   # Message system data
│   ├── message_history.json   # Message history
│   └── scheduled_messages.json # Scheduled messages
│
├── photos/                     # Photo storage directory
├── scripts/                    # System scripts
└── services/
    └── smart_frame_native.service  # Systemd service
```

---

## 🎨 Design Philosophy

### Retro Hardware Aesthetic
- **Monospace fonts only** (Courier New throughout)
- **Pure black backgrounds** (#000000)
- **Minimal color palette** (off-white, soft green, grays)
- **No gradients, shadows, or rounded corners**
- **Discrete state changes** - instant swaps, no animations
- **Text-based interfaces** - arrow selection, minimal graphics

### Performance
- **Native widgets** - No web rendering overhead
- **Efficient rendering** - QPainter for custom graphics
- **Low memory footprint** - Optimized for Raspberry Pi
- **Headless services** - mpv for music (no browser)

---

## 🛠️ Development

### Running in Development Mode

```bash
# Windowed mode for testing
python3 main.py

# With debug logging
python3 main.py --debug
```

### Adding New Voice Commands

1. Edit `config/voice_commands.json`:
```json
{
  "new command phrase": "action_identifier"
}
```

2. Add handler in `services/voice_service.py`:
```python
if action == "action_identifier":
    # Your action code
    self.navigate(AppState.VIEW_CUSTOM)
    self._speak("Action executed")
    return True
```

### Creating New Views

1. Create `ui/views/custom_view.py`:
```python
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QColor

class CustomView(QWidget):
    def __init__(self, app_state, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self.setStyleSheet("background-color: #000000;")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw your retro UI
```

2. Register in `ui/main_window.py`

---

## 🐛 Troubleshooting

### No Sound
```bash
# Check audio device
aplay -l

# Test mpv
mpv --no-video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Voice Control Not Working
```bash
# Test microphone
arecord -l

# Install dependencies
pip3 install SpeechRecognition pyttsx3 pyaudio
```

### Display Issues
```bash
# Check resolution
xrandr

# Set in config/settings.yaml
resolution:
  width: 1024
  height: 600
```

---

## 📝 License

MIT License - feel free to modify and distribute.

---

## 🙏 Acknowledgments

- PyQt5 for native widgets
- mpv for headless music playback
- Google Speech Recognition for voice control
- pyttsx3 for text-to-speech

---

**Enjoy your retro hardware smart frame! 🖼️**
