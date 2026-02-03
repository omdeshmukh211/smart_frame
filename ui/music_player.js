/**
 * Music Player Module
 * Manages the lightweight YouTube music player UI and API interactions
 */

const MusicPlayer = (function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        API_BASE: '/api/music',
        STATUS_POLL_INTERVAL: 2000, // 2 seconds
    };
    
    // State
    let state = {
        isOpen: false,
        isPlaying: false,
        isPaused: false,
        currentTrack: null,
        statusPollTimer: null,
    };
    
    // DOM Elements
    let elements = {};
    
    /**
     * Initialize the music player
     */
    function init() {
        cacheElements();
        attachEventListeners();
        console.log('Music Player initialized');
    }
    
    /**
     * Cache DOM element references
     */
    function cacheElements() {
        elements = {
            overlay: document.getElementById('music-player-overlay'),
            closeBtn: document.getElementById('music-player-close'),
            searchInput: document.getElementById('music-search-input'),
            searchBtn: document.getElementById('music-search-btn'),
            trackTitle: document.getElementById('music-track-title'),
            trackArtist: document.getElementById('music-track-artist'),
            noTrack: document.getElementById('music-no-track'),
            prevBtn: document.getElementById('music-btn-prev'),
            playPauseBtn: document.getElementById('music-btn-play-pause'),
            nextBtn: document.getElementById('music-btn-next'),
            playIcon: document.getElementById('music-icon-play'),
            pauseIcon: document.getElementById('music-icon-pause'),
            status: document.getElementById('music-status'),
        };
    }
    
    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        if (elements.closeBtn) {
            elements.closeBtn.addEventListener('click', close);
        }
        
        if (elements.searchBtn) {
            elements.searchBtn.addEventListener('click', handleSearch);
        }
        
        if (elements.searchInput) {
            elements.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleSearch();
                }
            });
        }
        
        if (elements.prevBtn) {
            elements.prevBtn.addEventListener('click', handlePrevious);
        }
        
        if (elements.playPauseBtn) {
            elements.playPauseBtn.addEventListener('click', handlePlayPause);
        }
        
        if (elements.nextBtn) {
            elements.nextBtn.addEventListener('click', handleNext);
        }
        
        // Close on overlay click (outside container)
        if (elements.overlay) {
            elements.overlay.addEventListener('click', (e) => {
                if (e.target === elements.overlay) {
                    close();
                }
            });
        }
    }
    
    /**
     * Open the music player overlay
     */
    function open() {
        if (state.isOpen) return;
        
        state.isOpen = true;
        
        if (elements.overlay) {
            elements.overlay.classList.add('active');
        }
        
        // Focus search input
        if (elements.searchInput) {
            setTimeout(() => elements.searchInput.focus(), 300);
        }
        
        // Start polling for status
        startStatusPolling();
        
        // Get initial status
        updateStatus();
    }
    
    /**
     * Close the music player overlay
     */
    function close() {
        if (!state.isOpen) return;
        
        state.isOpen = false;
        
        if (elements.overlay) {
            elements.overlay.classList.remove('active');
        }
        
        // Stop polling
        stopStatusPolling();
    }
    
    /**
     * Handle search button click
     */
    async function handleSearch() {
        const query = elements.searchInput?.value?.trim();
        
        if (!query) {
            showStatus('Please enter a song or artist name', 'error');
            return;
        }
        
        showStatus('Searching...', 'loading');
        setControlsDisabled(true);
        
        try {
            const response = await fetch(`${CONFIG.API_BASE}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('Playing...', 'success');
                updatePlayerState(data.status);
                
                // Clear search input
                if (elements.searchInput) {
                    elements.searchInput.value = '';
                }
            } else {
                showStatus(data.error || 'Failed to play track', 'error');
            }
        } catch (error) {
            console.error('Search error:', error);
            showStatus('Network error', 'error');
        } finally {
            setControlsDisabled(false);
        }
    }
    
    /**
     * Handle play/pause toggle
     */
    async function handlePlayPause() {
        if (!state.isPlaying && !state.isPaused) {
            showStatus('No track playing', 'error');
            return;
        }
        
        const endpoint = state.isPaused ? 'play' : 'pause';
        
        try {
            const response = await fetch(`${CONFIG.API_BASE}/${endpoint}`, {
                method: 'POST',
            });
            
            const data = await response.json();
            
            if (data.success) {
                updatePlayerState(data.status);
            }
        } catch (error) {
            console.error('Play/pause error:', error);
            showStatus('Control error', 'error');
        }
    }
    
    /**
     * Handle next track
     */
    async function handleNext() {
        showStatus('Loading next track...', 'loading');
        setControlsDisabled(true);
        
        try {
            const response = await fetch(`${CONFIG.API_BASE}/next`, {
                method: 'POST',
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('');
                updatePlayerState(data.status);
            } else {
                showStatus('No next track', 'error');
            }
        } catch (error) {
            console.error('Next error:', error);
            showStatus('Control error', 'error');
        } finally {
            setControlsDisabled(false);
        }
    }
    
    /**
     * Handle previous track
     */
    async function handlePrevious() {
        showStatus('Loading previous track...', 'loading');
        setControlsDisabled(true);
        
        try {
            const response = await fetch(`${CONFIG.API_BASE}/previous`, {
                method: 'POST',
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('');
                updatePlayerState(data.status);
            } else {
                showStatus('No previous track', 'error');
            }
        } catch (error) {
            console.error('Previous error:', error);
            showStatus('Control error', 'error');
        } finally {
            setControlsDisabled(false);
        }
    }
    
    /**
     * Update status from server
     */
    async function updateStatus() {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/status`);
            const data = await response.json();
            
            if (data.success) {
                updatePlayerState(data.status);
            }
        } catch (error) {
            console.error('Status update error:', error);
        }
    }
    
    /**
     * Update player state from status object
     */
    function updatePlayerState(status) {
        state.isPlaying = status.is_playing;
        state.isPaused = status.is_paused;
        state.currentTrack = status.current_track;
        
        updateNowPlaying();
        updatePlayPauseButton();
    }
    
    /**
     * Update now playing display
     */
    function updateNowPlaying() {
        if (state.currentTrack) {
            if (elements.trackTitle) {
                elements.trackTitle.textContent = state.currentTrack.title;
                elements.trackTitle.style.display = 'block';
            }
            
            if (elements.trackArtist) {
                elements.trackArtist.textContent = state.currentTrack.artist;
                elements.trackArtist.style.display = 'block';
            }
            
            if (elements.noTrack) {
                elements.noTrack.style.display = 'none';
            }
        } else {
            if (elements.trackTitle) {
                elements.trackTitle.style.display = 'none';
            }
            
            if (elements.trackArtist) {
                elements.trackArtist.style.display = 'none';
            }
            
            if (elements.noTrack) {
                elements.noTrack.style.display = 'block';
            }
        }
    }
    
    /**
     * Update play/pause button icon
     */
    function updatePlayPauseButton() {
        if (!elements.playIcon || !elements.pauseIcon) return;
        
        if (state.isPlaying && !state.isPaused) {
            // Show pause icon
            elements.playIcon.style.display = 'none';
            elements.pauseIcon.style.display = 'block';
        } else {
            // Show play icon
            elements.playIcon.style.display = 'block';
            elements.pauseIcon.style.display = 'none';
        }
    }
    
    /**
     * Show status message
     */
    function showStatus(message, type = '') {
        if (!elements.status) return;
        
        elements.status.textContent = message;
        elements.status.className = 'music-status';
        
        if (type) {
            elements.status.classList.add(type);
        }
        
        // Auto-clear success messages
        if (type === 'success') {
            setTimeout(() => {
                if (elements.status.textContent === message) {
                    elements.status.textContent = '';
                    elements.status.className = 'music-status';
                }
            }, 3000);
        }
    }
    
    /**
     * Enable/disable controls
     */
    function setControlsDisabled(disabled) {
        const controls = [
            elements.searchBtn,
            elements.prevBtn,
            elements.playPauseBtn,
            elements.nextBtn,
        ];
        
        controls.forEach(control => {
            if (control) {
                control.disabled = disabled;
            }
        });
    }
    
    /**
     * Start polling for status updates
     */
    function startStatusPolling() {
        stopStatusPolling();
        
        state.statusPollTimer = setInterval(() => {
            updateStatus();
        }, CONFIG.STATUS_POLL_INTERVAL);
    }
    
    /**
     * Stop polling for status updates
     */
    function stopStatusPolling() {
        if (state.statusPollTimer) {
            clearInterval(state.statusPollTimer);
            state.statusPollTimer = null;
        }
    }
    
    /**
     * Stop music playback
     */
    async function stop() {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/stop`, {
                method: 'POST',
            });
            
            const data = await response.json();
            
            if (data.success) {
                state.isPlaying = false;
                state.isPaused = false;
                state.currentTrack = null;
                updateNowPlaying();
                updatePlayPauseButton();
            }
        } catch (error) {
            console.error('Stop error:', error);
        }
    }
    
    // Public API
    return {
        init,
        open,
        close,
        stop,
        updateStatus,
    };
})();

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.MusicPlayer = MusicPlayer;
}
