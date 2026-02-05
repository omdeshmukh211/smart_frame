"""
Views Package
Screen layouts for different app modes - Retro Hardware Style.
"""

from .idle_view import IdleView
from .home_view import HomeView
from .menu_view import MenuView
from .photo_view import PhotoView
from .music_view import MusicView
from .settings_view import SettingsView
from .messages_view import MessagesView
from .games_view import GamesView

__all__ = [
    'IdleView',
    'HomeView',
    'MenuView',
    'PhotoView',
    'MusicView',
    'SettingsView',
    'MessagesView',
    'GamesView',
]
