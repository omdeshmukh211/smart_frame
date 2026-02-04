# PyQt5 UI Quick Reference

## 🚀 Quick Start

```bash
cd smart_frame
python3 main.py
```

## 🎨 UI Overview

### Idle Screen 🤖
- **Robot Face**: Blinks, yawns, sleeps
- **Sleep Mode**: 11 PM - 8 AM (closed eyes + ZZZ)
- **Tap Anywhere**: Wake to home screen

### Home Screen 🏠
- **Day Mode** (6 AM - 6 PM): Sun ☀️ + warm colors
- **Night Mode** (6 PM - 6 AM): Moon 🌙 + stars ✨
- **Large Clock**: HH:MM + date
- **Photo Frame**: Preview area (clickable)
- **5 Circular Buttons**:
  - 🎵 Music
  - 😴 Sleep
  - ⚙️ Settings
  - 🎮 Games
  - 💬 Messages

### Navigation
```
Idle → Tap → Home
Home → Music/Photos/Settings/Messages/Games
Any View → Sleep Button → Idle
Auto-Idle → 2 minutes of inactivity
```

## ⚙️ Configuration

### Edit `config/settings.yaml`

```yaml
# Idle timer (seconds)
idle_timeout: 120

# Display size
display_width: 1024
display_height: 600

# Photo slideshow
slideshow_interval: 600  # 10 minutes
photos_dir: photos/
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `ui/views/idle_view.py` | Robot face animation |
| `ui/views/home_view.py` | Day/night clock screen |
| `ui/views/messages_view.py` | Message library |
| `ui/views/games_view.py` | Game selection |
| `ui/main_window.py` | Navigation & idle timer |
| `models/app_state.py` | State management |

## 🎮 Keyboard Shortcuts

- **Ctrl+Q**: Quit
- **F11**: Toggle fullscreen
- **Click/Tap**: Wake from idle

## 🐛 Troubleshooting

### Robot face animation is slow
```python
# In idle_view.py, reduce timer frequency
self.float_timer.start(100)  # Was 50ms
```

### Stars cause high CPU
```python
# In home_view.py, reduce star count
for _ in range(10):  # Was 25
```

### Idle timeout not working
```bash
# Check settings.yaml
cat config/settings.yaml | grep idle_timeout

# Should show:
# idle_timeout: 120
```

## 📊 Performance Tips

### Raspberry Pi Optimization

1. **Reduce animation frequency**:
   ```python
   timer.start(100)  # Instead of 50
   ```

2. **Simplify gradients**:
   ```python
   # Use solid colors instead of gradients
   painter.fillRect(rect, QColor("#1a1a2e"))
   ```

3. **Lower star count**:
   ```python
   self.stars = []  # Disable stars entirely
   ```

## 📝 Adding Custom Views

### 1. Create view file
```python
# ui/views/my_view.py
from PyQt5.QtWidgets import QWidget
from models.app_state import AppState

class MyView(QWidget):
    def __init__(self, app_state, navigate_callback):
        super().__init__()
        self.app_state = app_state
        self.navigate = navigate_callback
        self._init_ui()
    
    def _init_ui(self):
        # Your UI code here
        pass
    
    def on_activate(self):
        print("View activated")
    
    def on_deactivate(self):
        print("View deactivated")
```

### 2. Register in AppState
```python
# models/app_state.py
VIEW_MY_VIEW = 'my_view'
```

### 3. Add to MainWindow
```python
# ui/main_window.py
from ui.views.my_view import MyView

# In _init_ui():
self.my_view = MyView(self.app_state, self._navigate)
self.views[AppState.VIEW_MY_VIEW] = self.my_view
self.stack.addWidget(self.my_view)
```

## 🎨 Styling Guide

### QSS (Qt Style Sheets)

```python
widget.setStyleSheet("""
    QWidget {
        background: #1a1a2e;
        color: white;
        font-size: 16px;
    }
    QPushButton {
        background: #2196F3;
        border-radius: 10px;
        padding: 15px;
    }
    QPushButton:hover {
        background: #1976D2;
    }
""")
```

### Custom Painting

```python
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Gradient background
    gradient = QLinearGradient(0, 0, self.width(), self.height())
    gradient.setColorAt(0, QColor("#1a1a2e"))
    gradient.setColorAt(1, QColor("#0f3460"))
    painter.fillRect(self.rect(), gradient)
    
    # Draw circle
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
    painter.drawEllipse(100, 100, 50, 50)
```

## 🔧 Common Tasks

### Change idle robot expression
Edit `ui/views/idle_view.py` in `paintEvent()` method

### Modify day/night threshold
```python
# In home_view.py
self.is_day_mode = 7 <= hour < 19  # 7 AM - 7 PM
```

### Adjust button layout
Edit `ui/views/home_view.py` in `_init_ui()` button section

### Add message source
Create/edit `messages/message_history.json`:
```json
{
  "messages": [
    {"text": "Hello!", "timestamp": "2026-02-04T10:00:00"}
  ]
}
```

## 📱 Messages API

### Message Format
```json
{
  "messages": [
    {
      "text": "Your message here",
      "timestamp": "2026-02-04T14:30:00",
      "sender": "Optional sender name"
    }
  ]
}
```

### Adding Messages Programmatically
```python
import json
from datetime import datetime
from pathlib import Path

messages_file = Path("messages/message_history.json")
messages_file.parent.mkdir(exist_ok=True)

# Load existing
data = {"messages": []}
if messages_file.exists():
    with open(messages_file, 'r') as f:
        data = json.load(f)

# Add new message
data["messages"].append({
    "text": "Hello from Python!",
    "timestamp": datetime.now().isoformat()
})

# Save
with open(messages_file, 'w') as f:
    json.dump(data, f, indent=2)
```

## 🎯 Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Idle Robot | ✅ Complete | All expressions working |
| Day/Night Mode | ✅ Complete | Auto-switching |
| Messages | ✅ Complete | View-only for now |
| Games | 🚧 In Progress | UI done, games TBD |
| Photo Slideshow | ✅ Complete | From existing code |
| Music Player | ✅ Complete | From existing code |
| Settings | ✅ Complete | From existing code |
| Idle Timer | ✅ Complete | Auto-return to idle |

## 📞 Need Help?

1. Check `PYQT5_UI_REVAMP.md` for detailed docs
2. Read `README_NATIVE.md` for architecture
3. Review PyQt5 examples in view files
4. Check logs: `data/logs.txt`

---

**Quick Tip**: Press **F11** to toggle fullscreen during development!
