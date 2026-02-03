/**
 * Smart Frame - Frontend Application
 * Handles UI updates, polling, and user interactions.
 */

// Configuration
const CONFIG = {
    API_BASE_URL: '',  // Same origin
    POLL_INTERVAL: 1000,  // 1 second
    MESSAGE_POLL_INTERVAL: 5000,  // 5 seconds
    MESSAGE_AUTO_DISMISS: 300,  // 5 minutes in seconds
    // Day/Night thresholds (24-hour format)
    DAY_START_HOUR: 6,   // 6 AM
    NIGHT_START_HOUR: 18, // 6 PM
};

// State
let currentState = 'IDLE';
let isSettingsOpen = false;
let pollTimer = null;
let messagePollTimer = null;
let messageAutoDismissTimer = null;
let messageCountdownInterval = null;
let messageSecondsRemaining = 0;

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
        timer: null,
        libraryBtn: null,
    },
    messageLibrary: {
        overlay: null,
        list: null,
        close: null,
    },
    buttons: {
        music: null,
        sleep: null,
        settings: null,
        games: null,
        messages: null,
    },
    games: {
        selectionOverlay: null,
        selectionClose: null,
        selectSnake: null,
        selectTictactoe: null,
        container: null,
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
    idle: {
        face: null,
    },
};

// Idle face state
let lastYawnTime = Date.now();
let lastHappyTime = Date.now();
const YAWN_INTERVAL = 20 * 60 * 1000; // 20 minutes in milliseconds
const YAWN_DURATION = 4000; // 4 seconds
const HAPPY_INTERVAL = 5 * 60 * 1000; // 5 minutes
const HAPPY_DURATION = 3000; // 3 seconds

/**
 * Initialize the application
 */
function init() {
    // Cache DOM elements
    cacheElements();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize music player
    if (window.MusicPlayer) {
        MusicPlayer.init();
    }
    
    // Start polling
    startPolling();
    
    // Start clock update
    updateClock();
    setInterval(updateClock, 1000);
    
    // Update sun/moon icon
    updateTimeIcon();
    setInterval(updateTimeIcon, 60000); // Check every minute
    
    // Initialize idle face animations
    initIdleFace();
    
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
    elements.message.timer = document.getElementById('message-timer');
    elements.message.libraryBtn = document.getElementById('message-library-btn');
    
    elements.messageLibrary.overlay = document.getElementById('message-library-overlay');
    elements.messageLibrary.list = document.getElementById('message-library-list');
    elements.messageLibrary.close = document.getElementById('message-library-close');
    
    elements.buttons.music = document.getElementById('btn-music');
    elements.buttons.sleep = document.getElementById('btn-sleep');
    elements.buttons.settings = document.getElementById('btn-settings');
    
    elements.settings.panel = document.getElementById('settings-panel');
    elements.settings.close = document.getElementById('settings-close');
    elements.settings.bluetooth = document.getElementById('bluetooth-toggle');
    elements.settings.brightness.slider = document.getElementById('brightness-slider');
    elements.settings.brightness.value = document.getElementById('brightness-value');
    elements.settings.volume.slider = document.getElementById('volume-slider');
    elements.settings.volume.value = document.getElementById('volume-value');
    
    // Game elements
    elements.buttons.games = document.getElementById('btn-games');
    elements.buttons.messages = document.getElementById('btn-messages');
    elements.games.selectionOverlay = document.getElementById('game-selection-overlay');
    elements.games.selectionClose = document.getElementById('game-selection-close');
    elements.games.selectSnake = document.getElementById('game-select-snake');
    elements.games.selectTictactoe1p = document.getElementById('game-select-tictactoe-1p');
    elements.games.selectTictactoe2p = document.getElementById('game-select-tictactoe-2p');
    elements.games.selectWordle = document.getElementById('game-select-wordle');
    elements.games.container = document.getElementById('game-container');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Idle screen tap handler
    elements.screens.idle.addEventListener('click', handleIdleTap);
    
    // Message dismiss and library
    elements.message.dismiss.addEventListener('click', dismissMessage);
    elements.message.libraryBtn.addEventListener('click', () => {
        dismissMessage();
        openMessageLibrary();
    });
    
    // Message library
    elements.messageLibrary.close.addEventListener('click', closeMessageLibrary);
    elements.messageLibrary.overlay.addEventListener('click', (e) => {
        if (e.target === elements.messageLibrary.overlay) {
            closeMessageLibrary();
        }
    });
    
    // Action buttons
    elements.buttons.music.addEventListener('click', handleMusicButton);
    elements.buttons.sleep.addEventListener('click', handleSleepButton);
    elements.buttons.settings.addEventListener('click', openSettings);
    elements.buttons.messages.addEventListener('click', openMessageLibrary);
    
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
    
    // Games button and selection
    if (elements.buttons.games) {
        elements.buttons.games.addEventListener('click', openGameSelection);
    }
    
    if (elements.games.selectionClose) {
        elements.games.selectionClose.addEventListener('click', closeGameSelection);
    }
    
    if (elements.games.selectionOverlay) {
        elements.games.selectionOverlay.addEventListener('click', (e) => {
            if (e.target === elements.games.selectionOverlay) {
                closeGameSelection();
            }
        });
    }
    
    if (elements.games.selectSnake) {
        elements.games.selectSnake.addEventListener('click', () => {
            if (typeof GameManager !== 'undefined') {
                GameManager.startGame('snake');
            }
        });
    }
    
    if (elements.games.selectTictactoe1p) {
        elements.games.selectTictactoe1p.addEventListener('click', () => {
            if (typeof GameManager !== 'undefined') {
                GameManager.startGame('tictactoe', { mode: '1p' });
            }
        });
    }
    
    if (elements.games.selectTictactoe2p) {
        elements.games.selectTictactoe2p.addEventListener('click', () => {
            if (typeof GameManager !== 'undefined') {
                GameManager.startGame('tictactoe', { mode: '2p' });
            }
        });
    }
    
    if (elements.games.selectWordle) {
        elements.games.selectWordle.addEventListener('click', () => {
            if (typeof GameManager !== 'undefined') {
                GameManager.startGame('wordle');
            }
        });
    }
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
            updateState(data.state, true);
        } else {
            // Backend returned error, fallback to local state change
            console.warn('Tap endpoint returned error, using local fallback');
            updateState('CLOCK', true);
        }
    } catch (error) {
        // Backend not available, switch locally
        console.warn('Tap request failed, using local fallback:', error.message);
        updateState('CLOCK', true);
    }
}

/**
 * Handle Music button - open music player overlay
 */
async function handleMusicButton() {
    // Open the new lightweight music player overlay
    if (window.MusicPlayer) {
        MusicPlayer.open();
    } else {
        console.error('MusicPlayer not initialized');
    }
}

/**
 * Handle Sleep button - return to idle state
 */
async function handleSleepButton() {
    try {
        // Stop music player if active
        if (window.MusicPlayer) {
            await MusicPlayer.stop();
        }
        
        // If music is playing, stop it first (API call)
        await fetch('/api/music/stop', {
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
 * Open game selection overlay
 */
function openGameSelection() {
    if (elements.games.selectionOverlay) {
        elements.games.selectionOverlay.classList.remove('hidden');
    }
}

/**
 * Close game selection overlay
 */
function closeGameSelection() {
    if (elements.games.selectionOverlay) {
        elements.games.selectionOverlay.classList.add('hidden');
    }
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
    // Don't update state while a game is active (games manage their own state)
    if (typeof GameManager !== 'undefined' && GameManager.isGameActive()) {
        return;
    }
    
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
function updateState(newState, force = false) {
    if (newState === currentState && !force) return;
    
    currentState = newState;
    
    // Hide all screens
    Object.values(elements.screens).forEach(screen => {
        if (screen) screen.classList.remove('active');
    });
    
    // Show appropriate screen
    switch (newState) {
        case 'IDLE':
            if (elements.screens.idle) elements.screens.idle.classList.add('active');
            break;
        case 'CLOCK':
            if (elements.screens.clock) elements.screens.clock.classList.add('active');
            break;
        case 'MUSIC':
            if (elements.screens.music) elements.screens.music.classList.add('active');
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
 * Show a message overlay with 5-minute auto-dismiss
 */
function showMessage(message) {
    // Clear any existing timers
    clearMessageTimers();
    
    elements.message.content.textContent = message;
    elements.message.overlay.classList.remove('hidden');
    
    // Start 5-minute auto-dismiss countdown
    messageSecondsRemaining = CONFIG.MESSAGE_AUTO_DISMISS;
    updateMessageTimerDisplay();
    
    messageCountdownInterval = setInterval(() => {
        messageSecondsRemaining--;
        updateMessageTimerDisplay();
        
        if (messageSecondsRemaining <= 0) {
            dismissMessage();
        }
    }, 1000);
    
    // Pause game if running
    if (typeof GameManager !== 'undefined' && GameManager.isGameActive()) {
        GameManager.pauseGame();
    }
}

/**
 * Update the countdown timer display
 */
function updateMessageTimerDisplay() {
    if (elements.message.timer) {
        const minutes = Math.floor(messageSecondsRemaining / 60);
        const seconds = messageSecondsRemaining % 60;
        const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        elements.message.timer.textContent = `Auto-dismiss in ${timeStr}`;
    }
}

/**
 * Clear message auto-dismiss timers
 */
function clearMessageTimers() {
    if (messageCountdownInterval) {
        clearInterval(messageCountdownInterval);
        messageCountdownInterval = null;
    }
    if (messageAutoDismissTimer) {
        clearTimeout(messageAutoDismissTimer);
        messageAutoDismissTimer = null;
    }
}

/**
 * Dismiss the message overlay
 */
function dismissMessage() {
    clearMessageTimers();
    elements.message.overlay.classList.add('hidden');
    
    // Clear the message on backend
    fetch('/message/clear', { method: 'POST' }).catch(() => {});
    
    // Resume game if it was paused
    if (typeof GameManager !== 'undefined' && GameManager.isGameActive()) {
        GameManager.resumeGame();
    }
}

/**
 * Open message library overlay
 */
async function openMessageLibrary() {
    elements.messageLibrary.overlay.classList.remove('hidden');
    await loadMessageHistory();
}

/**
 * Close message library overlay
 */
function closeMessageLibrary() {
    elements.messageLibrary.overlay.classList.add('hidden');
}

/**
 * Load and display message history
 */
async function loadMessageHistory() {
    const listEl = elements.messageLibrary.list;
    
    try {
        const response = await fetch('/message/history');
        if (!response.ok) throw new Error('Failed to fetch');
        
        const data = await response.json();
        const messages = data.messages || [];
        
        if (messages.length === 0) {
            listEl.innerHTML = '<div class="message-library-empty">No messages yet</div>';
            return;
        }
        
        // Sort by delivered_at descending (newest first)
        messages.sort((a, b) => {
            return new Date(b.delivered_at) - new Date(a.delivered_at);
        });
        
        listEl.innerHTML = messages.map(msg => {
            const deliveredDate = formatMessageDate(msg.delivered_at);
            const scheduledDate = msg.scheduled_at || '';
            
            return `
                <div class="message-library-item">
                    <div class="message-library-item-header">
                        <span class="message-library-from">${escapeHtml(msg.from || 'Unknown')}</span>
                        <span class="message-library-date">${deliveredDate}</span>
                    </div>
                    <div class="message-library-text">${escapeHtml(msg.text || '')}</div>
                    ${scheduledDate ? `<div class="message-library-scheduled">Scheduled: ${scheduledDate}</div>` : ''}
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load message history:', error);
        listEl.innerHTML = '<div class="message-library-empty">Failed to load messages</div>';
    }
}

/**
 * Format message date for display
 */
function formatMessageDate(dateStr) {
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            // Today - show time
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    } catch {
        return dateStr;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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

// ============================================================================
// Idle Face Animation Functions
// ============================================================================

/**
 * Initialize idle face animations
 */
function initIdleFace() {
    // Update face state immediately
    updateIdleFaceState();
    
    // Check face state every minute
    setInterval(updateIdleFaceState, 60000);
    
    // Check for yawn trigger every 30 seconds
    setInterval(checkYawnTrigger, 30000);
    
    // Check for happy expression every 30 seconds
    setInterval(checkHappyTrigger, 30000);
}

/**
 * Update idle face state based on time of day
 * Sleep mode: 11 PM (23:00) to 8 AM (08:00)
 */
function updateIdleFaceState() {
    const idleScreen = elements.screens.idle;
    if (!idleScreen) return;
    
    const now = new Date();
    const hour = now.getHours();
    
    // Sleep mode: 11 PM (23) to 8 AM (8)
    const isSleepTime = hour >= 23 || hour < 8;
    
    if (isSleepTime) {
        idleScreen.classList.add('sleep-mode');
        idleScreen.classList.remove('yawning');
        idleScreen.classList.remove('happy');
    } else {
        idleScreen.classList.remove('sleep-mode');
    }
}

/**
 * Check if it's time to trigger a yawn
 * Yawns every 20 minutes when not in sleep mode
 */
function checkYawnTrigger() {
    const idleScreen = elements.screens.idle;
    if (!idleScreen) return;
    
    // Don't yawn if in sleep mode or not on idle screen
    if (idleScreen.classList.contains('sleep-mode')) return;
    if (!idleScreen.classList.contains('active')) return;
    if (idleScreen.classList.contains('happy')) return;
    
    const now = Date.now();
    
    // Check if 20 minutes have passed since last yawn
    if (now - lastYawnTime >= YAWN_INTERVAL) {
        triggerYawn();
        lastYawnTime = now;
    }
}

/**
 * Check if it's time to show happy expression
 */
function checkHappyTrigger() {
    const idleScreen = elements.screens.idle;
    if (!idleScreen) return;
    
    // Don't be happy if in sleep mode or yawning
    if (idleScreen.classList.contains('sleep-mode')) return;
    if (!idleScreen.classList.contains('active')) return;
    if (idleScreen.classList.contains('yawning')) return;
    
    const now = Date.now();
    
    // Check if 5 minutes have passed since last happy moment
    if (now - lastHappyTime >= HAPPY_INTERVAL) {
        triggerHappy();
        lastHappyTime = now;
    }
}

/**
 * Trigger a yawn animation
 */
function triggerYawn() {
    const idleScreen = elements.screens.idle;
    if (!idleScreen) return;
    
    // Add yawning class
    idleScreen.classList.add('yawning');
    
    // Remove yawning class after animation completes
    setTimeout(() => {
        idleScreen.classList.remove('yawning');
    }, YAWN_DURATION);
}

/**
 * Trigger happy expression (^^ eyes)
 */
function triggerHappy() {
    const idleScreen = elements.screens.idle;
    if (!idleScreen) return;
    
    // Add happy class
    idleScreen.classList.add('happy');
    
    // Remove happy class after duration
    setTimeout(() => {
        idleScreen.classList.remove('happy');
    }, HAPPY_DURATION);
}

/**
 * Force a yawn (can be called for testing)
 */
function forceYawn() {
    triggerYawn();
    lastYawnTime = Date.now();
}

/**
 * Force happy expression (can be called for testing)
 */
function forceHappy() {
    triggerHappy();
    lastHappyTime = Date.now();
}

/**
 * Force sleep mode toggle (can be called for testing)
 */
function toggleSleepMode() {
    const idleScreen = elements.screens.idle;
    if (!idleScreen) return;
    
    idleScreen.classList.toggle('sleep-mode');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
