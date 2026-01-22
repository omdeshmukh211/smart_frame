/**
 * Smart Frame - Frontend Application
 * Handles UI updates, polling, and user interactions.
 */

// Configuration
const CONFIG = {
    API_BASE_URL: '',  // Same origin
    POLL_INTERVAL: 1000,  // 1 second
    MESSAGE_POLL_INTERVAL: 5000,  // 5 seconds
    // Day/Night thresholds (24-hour format)
    DAY_START_HOUR: 6,   // 6 AM
    NIGHT_START_HOUR: 18, // 6 PM
};

// State
let currentState = 'IDLE';
let isSettingsOpen = false;
let pollTimer = null;
let messagePollTimer = null;

// DOM Elements
const elements = {
    app: null,
    screens: {
        idle: null,
        clock: null,
        music: null,
    },
    clock: {
        hours: null,
        minutes: null,
        date: null,
    },
    timeIcon: {
        sun: null,
        moon: null,
    },
    music: {
        artist: null,
    },
    message: {
        overlay: null,
        content: null,
        dismiss: null,
    },
    buttons: {
        music: null,
        search: null,
        sleep: null,
        settings: null,
    },
    settings: {
        panel: null,
        close: null,
        bluetooth: null,
        brightness: {
            slider: null,
            value: null,
        },
        volume: {
            slider: null,
            value: null,
        },
    },
};

/**
 * Initialize the application
 */
function init() {
    // Cache DOM elements
    cacheElements();
    
    // Setup event listeners
    setupEventListeners();
    
    // Start polling
    startPolling();
    
    // Start clock update
    updateClock();
    setInterval(updateClock, 1000);
    
    // Update sun/moon icon
    updateTimeIcon();
    setInterval(updateTimeIcon, 60000); // Check every minute
    
    console.log('Smart Frame initialized');
}

/**
 * Cache DOM element references
 */
function cacheElements() {
    elements.app = document.getElementById('app');
    
    elements.screens.idle = document.getElementById('idle-screen');
    elements.screens.clock = document.getElementById('clock-screen');
    elements.screens.music = document.getElementById('music-screen');
    
    elements.clock.hours = document.getElementById('clock-hours');
    elements.clock.minutes = document.getElementById('clock-minutes');
    elements.clock.date = document.getElementById('clock-date');
    
    elements.timeIcon.sun = document.getElementById('sun-icon');
    elements.timeIcon.moon = document.getElementById('moon-icon');
    
    elements.music.artist = document.getElementById('music-artist');
    
    elements.message.overlay = document.getElementById('message-overlay');
    elements.message.content = document.getElementById('message-content');
    elements.message.dismiss = document.getElementById('message-dismiss');
    
    elements.buttons.music = document.getElementById('btn-music');
    elements.buttons.search = document.getElementById('btn-search');
    elements.buttons.sleep = document.getElementById('btn-sleep');
    elements.buttons.settings = document.getElementById('btn-settings');
    
    elements.settings.panel = document.getElementById('settings-panel');
    elements.settings.close = document.getElementById('settings-close');
    elements.settings.bluetooth = document.getElementById('bluetooth-toggle');
    elements.settings.brightness.slider = document.getElementById('brightness-slider');
    elements.settings.brightness.value = document.getElementById('brightness-value');
    elements.settings.volume.slider = document.getElementById('volume-slider');
    elements.settings.volume.value = document.getElementById('volume-value');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Idle screen tap handler
    elements.screens.idle.addEventListener('click', handleIdleTap);
    
    // Message dismiss
    elements.message.dismiss.addEventListener('click', dismissMessage);
    
    // Action buttons
    elements.buttons.music.addEventListener('click', handleMusicButton);
    elements.buttons.search.addEventListener('click', handleSearchButton);
    elements.buttons.sleep.addEventListener('click', handleSleepButton);
    elements.buttons.settings.addEventListener('click', openSettings);
    
    // Settings panel
    elements.settings.close.addEventListener('click', closeSettings);
    elements.settings.panel.addEventListener('click', (e) => {
        // Close if clicking outside the container
        if (e.target === elements.settings.panel) {
            closeSettings();
        }
    });
    
    // Brightness slider
    elements.settings.brightness.slider.addEventListener('input', (e) => {
        const value = e.target.value;
        elements.settings.brightness.value.textContent = `${value}%`;
    });
    
    elements.settings.brightness.slider.addEventListener('change', (e) => {
        setBrightness(parseInt(e.target.value));
    });
    
    // Volume slider
    elements.settings.volume.slider.addEventListener('input', (e) => {
        const value = e.target.value;
        elements.settings.volume.value.textContent = `${value}%`;
    });
    
    elements.settings.volume.slider.addEventListener('change', (e) => {
        setVolume(parseInt(e.target.value));
    });
    
    // Bluetooth toggle
    elements.settings.bluetooth.addEventListener('change', (e) => {
        toggleBluetooth(e.target.checked);
    });
}

/**
 * Handle tap on idle screen - go to clock
 */
async function handleIdleTap() {
    try {
        const response = await fetch('/tap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        
        if (response.ok) {
            const data = await response.json();
            updateState(data.state);
        }
    } catch (error) {
        console.error('Tap request failed:', error);
    }
}

/**
 * Handle Music button - open YouTube Music
 */
async function handleMusicButton() {
    try {
        const response = await fetch('/music/play', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });
        
        if (response.ok) {
            const data = await response.json();
            updateState(data.state);
        }
    } catch (error) {
        console.error('Music request failed:', error);
    }
}

/**
 * Handle Search button - open web search
 */
function handleSearchButton() {
    // Open a web search in a new window/tab
    // Could be Google, DuckDuckGo, or a custom search page
    window.open('https://www.google.com', '_blank');
}

/**
 * Handle Sleep button - return to idle state
 */
async function handleSleepButton() {
    try {
        // If music is playing, stop it first
        await fetch('/music/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        
        // Then explicitly set state to IDLE via tap (which toggles)
        // Or we could add a dedicated /sleep endpoint
        const response = await fetch('/state');
        if (response.ok) {
            const data = await response.json();
            if (data.state === 'CLOCK') {
                // Tap to toggle to IDLE
                await fetch('/tap', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
            }
            updateState('IDLE');
        }
    } catch (error) {
        console.error('Sleep request failed:', error);
    }
}

/**
 * Open settings panel
 */
function openSettings() {
    elements.settings.panel.classList.remove('hidden');
    isSettingsOpen = true;
}

/**
 * Close settings panel
 */
function closeSettings() {
    elements.settings.panel.classList.add('hidden');
    isSettingsOpen = false;
}

/**
 * Toggle Bluetooth
 */
async function toggleBluetooth(enabled) {
    try {
        await fetch('/bluetooth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled }),
        });
        console.log('Bluetooth:', enabled ? 'enabled' : 'disabled');
    } catch (error) {
        console.error('Failed to toggle bluetooth:', error);
    }
}

/**
 * Start polling the backend for state updates
 */
function startPolling() {
    // Poll state
    pollTimer = setInterval(pollState, CONFIG.POLL_INTERVAL);
    
    // Poll messages
    messagePollTimer = setInterval(pollMessages, CONFIG.MESSAGE_POLL_INTERVAL);
    
    // Initial poll
    pollState();
    pollMessages();
}

/**
 * Poll the backend for current state
 */
async function pollState() {
    try {
        const response = await fetch('/state');
        if (response.ok) {
            const data = await response.json();
            updateState(data.state);
            
            if (data.artist) {
                elements.music.artist.textContent = data.artist;
            }
        }
    } catch (error) {
        console.error('State poll failed:', error);
    }
}

/**
 * Poll for active messages
 */
async function pollMessages() {
    try {
        const response = await fetch('/message/active');
        if (response.ok) {
            const data = await response.json();
            if (data.message) {
                showMessage(data.message);
            }
        }
    } catch (error) {
        console.error('Message poll failed:', error);
    }
}

/**
 * Update the UI based on state
 */
function updateState(newState) {
    if (newState === currentState) return;
    
    currentState = newState;
    
    // Hide all screens
    Object.values(elements.screens).forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Show appropriate screen
    switch (newState) {
        case 'IDLE':
            elements.screens.idle.classList.add('active');
            break;
        case 'CLOCK':
            elements.screens.clock.classList.add('active');
            break;
        case 'MUSIC':
            elements.screens.music.classList.add('active');
            break;
    }
    
    console.log('State updated:', newState);
}

/**
 * Update clock display
 */
function updateClock() {
    const now = new Date();
    
    // Hours (without leading zero for single digits)
    const hours = now.getHours();
    const hours12 = hours % 12 || 12;
    elements.clock.hours.textContent = hours12;
    
    // Minutes (with leading zero)
    const minutes = now.getMinutes().toString().padStart(2, '0');
    elements.clock.minutes.textContent = minutes;
    
    // Date: "Sat 29 Jan 2026"
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const dayName = days[now.getDay()];
    const dayNum = now.getDate();
    const monthName = months[now.getMonth()];
    const year = now.getFullYear();
    
    elements.clock.date.textContent = `${dayName} ${dayNum} ${monthName} ${year}`;
}

/**
 * Update sun/moon icon and background based on time of day
 */
function updateTimeIcon() {
    const now = new Date();
    const hour = now.getHours();
    
    const isDaytime = hour >= CONFIG.DAY_START_HOUR && hour < CONFIG.NIGHT_START_HOUR;
    const starsContainer = document.getElementById('stars-container');
    
    if (isDaytime) {
        // Day mode
        elements.timeIcon.sun.classList.remove('hidden');
        elements.timeIcon.moon.classList.add('hidden');
        elements.screens.clock.classList.add('day-mode');
        elements.screens.clock.classList.remove('night-mode');
        if (starsContainer) starsContainer.classList.add('hidden');
    } else {
        // Night mode
        elements.timeIcon.sun.classList.add('hidden');
        elements.timeIcon.moon.classList.remove('hidden');
        elements.screens.clock.classList.add('night-mode');
        elements.screens.clock.classList.remove('day-mode');
        if (starsContainer) starsContainer.classList.remove('hidden');
    }
}

/**
 * Show a message overlay
 */
function showMessage(message) {
    elements.message.content.textContent = message;
    elements.message.overlay.classList.remove('hidden');
}

/**
 * Dismiss the message overlay
 */
function dismissMessage() {
    elements.message.overlay.classList.add('hidden');
}

/**
 * Set brightness level
 */
async function setBrightness(level) {
    try {
        await fetch('/brightness', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level }),
        });
    } catch (error) {
        console.error('Failed to set brightness:', error);
    }
}

/**
 * Set volume level
 */
async function setVolume(level) {
    try {
        await fetch('/volume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level }),
        });
    } catch (error) {
        console.error('Failed to set volume:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
