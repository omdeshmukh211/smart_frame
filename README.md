# Smart Frame

A smart display system with voice control, dynamic clock display, and music playback capabilities. Features day/night mode with animated sun/moon icons and a beautiful visual experience.

---

## 🆕 New Features

### 📩 Message System
- Send messages to the frame via the API or UI.
- Messages are displayed on the screen and can be managed from the backend.
- Message history is stored in `data/messages.txt`.

### 🎵 YouTube Music Integration
- Press the **Music** button or use a voice command to open YouTube Music in Chromium.
- If Chromium is already open on YouTube Music, it will not open a new window (idempotent behavior).
- Voice commands like "play coldplay" will search and auto-play the top result on YouTube Music.
- Chromium opens in full-screen (kiosk) mode and is brought to the foreground.

### 🗣️ Voice Command Pipeline
- **Wake phrase gated:** Only processes speech that starts with a configurable wake phrase (see `config/voice_triggers.json`).
- **Configurable commands:** All voice commands and their actions are mapped in `config/voice_commands.json`.
- **Offline speech-to-text:** Uses Vosk for local, offline speech recognition (no cloud required).
- **Pipeline:**
   1. Capture speech from microphone
   2. Convert to text (STT)
   3. Normalize and check for wake phrase
   4. Parse command and execute mapped action
   5. Optional spoken feedback (TTS stub included)
- **Safe and robust:** Ignores speech without wake phrase, never executes partial/unsafe commands, and runs all actions in background threads.
- **Easy to extend:** Add new wake phrases or commands by editing the JSON config files—no code changes needed.

#### Example Wake Phrase Config (`config/voice_triggers.json`):
```json
{
   "wake_phrases": [
      "hey om",
      "hello om"
   ]
}
```

#### Example Command Map (`config/voice_commands.json`):
```json
{
   "play music": "open_youtube_music",
   "play coldplay": "play_youtube_music_search",
   "show messages": "open_message_library",
   "what time is it": "speak_time",
   "go to sleep": "enter_idle",
   "play snake": "launch_snake_game"
}
```

#### Example Voice Usage
- "Hey Om, play music"
- "Hello Om, play Coldplay"
- "Hey Om, what time is it?"
- "Hey Om, show messages"

#### Voice Pipeline Files
- `voice/voice_listener.py` — Main pipeline (STT, wake phrase, command parsing, action dispatch)
- `voice/command_parser.py` — Command matching logic
- `voice/actions.py` — Action implementations (background execution, TTS feedback)
- `voice/responses.py` — Simple TTS stub
- `backend/music_controller.py` — Chromium/YouTube Music open/search/autoplay logic

#### Requirements
- Add to `requirements.txt`:
   - `vosk`
   - `pyaudio`
   - (optional) `pyttsx3` for TTS

#### To Run Voice Listener
```bash
cd voice
python3 voice_listener.py
```

---

## 📁 Project Structure

```
smart_frame/
│
├── app.py                    # Main Flask server
│
├── config/
│   ├── settings.yaml         # Configuration settings
│   └── constants.py          # State constants
│
├── backend/
│   ├── state_manager.py      # System state management
│   ├── message_manager.py    # Message handling and storage
│   ├── music_controller.py   # Music playback control
│   └── system_controls.py    # Volume, brightness & Bluetooth control
│
├── voice/
│   ├── voice_listener.py     # Speech recognition
│   ├── command_parser.py     # Intent parsing
│   ├── actions.py            # Intent execution
│   └── responses.py          # Voice response templates
│
├── ui/
│   ├── index.html            # Main UI page
│   ├── app.js                # Frontend JavaScript
│   ├── style.css             # Styles with day/night themes
│   └── assets/               # Static assets
│       ├── idle/
│       ├── clock/
│       └── icons/
│
├── scripts/
│   ├── start_music.sh        # Launch YouTube Music
│   ├── stop_music.sh         # Stop music playback
│   └── set_volume.sh         # Set system volume
│
├── data/
│   ├── messages.txt          # Message history
│   └── logs.txt              # Application logs
│
├── services/
│   ├── app.service           # systemd service for Flask
│   └── voice.service         # systemd service for voice
│
└── README.md                 # This file
```

## 🖼️ Clock UI Features

### Day/Night Mode

The clock screen automatically switches between day and night modes based on time:

#### ☀️ Day Mode (6 AM - 6 PM)
- **Animated Sun**: Large sun icon with rotating rays and pulsing glow
- **Warm Background**: Golden yellow gradient creating a sunny atmosphere
- **Light UI**: Dark text on warm background

#### 🌙 Night Mode (6 PM - 6 AM)
- **Moon Icon**: Crescent moon with craters and soft glow
- **Starry Background**: Deep space gradient with twinkling stars
- **Dark UI**: White text and borders for contrast

### Clock Layout

```
┌─────────────────────────────────────────────────────────┐
│  ☀️/🌙                                                   │
│  (sun/moon)         ┌─────────────────────┐             │
│                     │    Photo Frame      │             │
│   9:30              │       Loop          │             │
│                     └─────────────────────┘             │
│   Sat 29 Jan 2026                                       │
│                      (Music) (Search) (Sleep) (Settings)│
└─────────────────────────────────────────────────────────┘
```

### Action Buttons

| Button | Function |
|--------|----------|
| **Music** | Opens YouTube Music for playback |
| **Search** | Opens web search (Google) |
| **Sleep** | Returns to idle state |
| **Settings** | Opens settings panel |

### Settings Panel

- **Bluetooth**: Toggle on/off
- **Brightness**: Slider (0-100%)
- **Volume**: Slider (0-100%)

### Photo Frame (Placeholder)

Reserved area for future photo slideshow functionality.

## 🏗️ Architecture

### System States

The system operates in three states:

- **IDLE**: Default state showing idle animation with pulsing circle
- **CLOCK**: Shows clock display with day/night theme (auto-returns to IDLE after 120s)
- **MUSIC**: Music playback mode (no auto-timeout)

### Components

1. **Flask Backend (`app.py`)**: Central server managing state and exposing REST APIs
2. **Voice Module**: Separate process for speech recognition and command execution
3. **Frontend UI**: Single-page app that polls backend for state updates

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/state` | GET | Get current system state |
| `/tap` | POST | Handle screen tap (toggle IDLE/CLOCK) |
| `/message` | POST | Set a new message |
| `/message/active` | GET | Get active message |
| `/music/play` | POST | Start music playback |
| `/music/stop` | POST | Stop music playback |
| `/volume` | POST | Set system volume |
| `/brightness` | POST | Set display brightness |
| `/bluetooth` | POST | Toggle Bluetooth on/off |

## 🚀 Manual Setup

### Prerequisites

- Python 3.7+
- pip
- Chromium browser (for music playback)
- Audio system (ALSA/PulseAudio/PipeWire)

### Installation

1. **Clone or copy the project**:
   ```bash
   cd /home/pi
   cp -r smart_frame /home/pi/smart_frame
   ```

2. **Install Python dependencies**:
   ```bash
   cd smart_frame
   pip3 install flask pyyaml
   ```

3. **Install voice dependencies** (optional):
   ```bash
   pip3 install SpeechRecognition pyaudio pyttsx3
   sudo apt-get install portaudio19-dev
   ```

4. **Make scripts executable**:
   ```bash
   chmod +x scripts/*.sh
   ```

### Running Manually

1. **Start the Flask server**:
   ```bash
   python3 app.py
   ```
   The server will be available at `http://localhost:5000`

2. **Start the voice listener** (in a separate terminal):
   ```bash
   cd voice
   python3 voice_listener.py
   ```

## ⚙️ systemd Services

### Enable Services

1. **Copy service files**:
   ```bash
   sudo cp services/app.service /etc/systemd/system/
   sudo cp services/voice.service /etc/systemd/system/
   ```

2. **Update paths** (if not using `/home/pi`):
   ```bash
   sudo nano /etc/systemd/system/app.service
   sudo nano /etc/systemd/system/voice.service
   ```

3. **Reload systemd**:
   ```bash
   sudo systemctl daemon-reload
   ```

4. **Enable and start services**:
   ```bash
   sudo systemctl enable app.service
   sudo systemctl enable voice.service
   sudo systemctl start app.service
   sudo systemctl start voice.service
   ```

### Service Management

```bash
# Check status
sudo systemctl status app.service
sudo systemctl status voice.service

# View logs
sudo journalctl -u app.service -f
sudo journalctl -u voice.service -f

# Restart services
sudo systemctl restart app.service
sudo systemctl restart voice.service

# Stop services
sudo systemctl stop app.service
sudo systemctl stop voice.service
```

## 🎤 Voice Commands

| Command | Action |
|---------|--------|
| "Hey smart frame" | Wake/greeting |
| "What time is it" | Speak current time |
| "Show clock" | Display clock |
| "Play [artist]" | Play music |
| "Stop music" | Stop playback |
| "Volume [0-100]" | Set volume |
| "Brightness [0-100]" | Set brightness |

## 🔧 Configuration

Edit `config/settings.yaml`:

```yaml
clock_timeout: 120      # Seconds before clock returns to idle
message_timeout: 300    # Seconds before message expires
default_volume: 70      # Default volume level (0-100)
default_brightness: 100 # Default brightness level (0-100)
```

### Day/Night Time Thresholds

Edit in `ui/app.js`:

```javascript
const CONFIG = {
    DAY_START_HOUR: 6,   // 6 AM - Switch to day mode
    NIGHT_START_HOUR: 18, // 6 PM - Switch to night mode
};
```

## 📝 Notes

- Day/night mode switches automatically based on system time
- Sun rays animate with a slow rotation effect
- Stars twinkle with staggered animations in night mode
- Photo frame area is a placeholder for future photo slideshow feature
- Voice module runs independently from UI
- Scripts are designed for Linux (Raspberry Pi)
- Adjust display output name in `system_controls.py` for brightness

## 🚀 Future Enhancements

- [ ] Weather-based mood changes (cloudy sun, rainy, etc.)
- [ ] Photo frame with slideshow from local folder or cloud
- [ ] Additional themes and color schemes
- [ ] Alarm/timer functionality
- [ ] Calendar integration

## 🐛 Troubleshooting

### Flask server won't start
- Check Python version: `python3 --version`
- Install dependencies: `pip3 install flask pyyaml`

### Voice recognition not working
- Check microphone: `arecord -l`
- Install audio dependencies: `sudo apt-get install portaudio19-dev`
- Test with: `python3 -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"`

### Music not playing
- Check Chromium: `which chromium-browser`
- Test script: `./scripts/start_music.sh "test"`

### Volume control not working
- Check audio system: `amixer` or `pactl`
- List sinks: `pactl list sinks short`

### Bluetooth not working
- Check bluetoothctl: `bluetoothctl show`
- Check rfkill: `rfkill list bluetooth`
