/**
 * Game Manager - Central controller for games
 * Handles game lifecycle, inactivity timeout, and message overlay integration
 */

const GameManager = (function() {
    // Private state
    let currentGame = null;
    let inactivityTimer = null;
    let isPaused = false;
    const INACTIVITY_TIMEOUT = 60000; // 60 seconds
    
    // Game registry
    const games = {};
    
    /**
     * Register a game with the manager
     */
    function registerGame(name, gameInstance) {
        games[name] = gameInstance;
    }
    
    /**
     * Start a game by name
     * @param {string} gameName - Name of the game to start
     * @param {Object} options - Options to pass to the game's init function
     */
    function startGame(gameName, options = {}) {
        if (!games[gameName]) {
            console.error(`Game "${gameName}" not found`);
            return false;
        }
        
        // Exit current game if any
        if (currentGame) {
            exitGame(false);
        }
        
        currentGame = gameName;
        isPaused = false;
        
        // Show game container
        const gameContainer = document.getElementById('game-container');
        if (gameContainer) {
            gameContainer.classList.remove('hidden');
        }
        
        // Hide game selection overlay
        const gameSelection = document.getElementById('game-selection-overlay');
        if (gameSelection) {
            gameSelection.classList.add('hidden');
        }
        
        // Initialize and start the game
        try {
            games[gameName].init(options);
            games[gameName].start();
            resetInactivityTimer();
            console.log(`Started game: ${gameName}`, options);
            return true;
        } catch (error) {
            console.error(`Failed to start game ${gameName}:`, error);
            exitGame(false);
            return false;
        }
    }
    
    /**
     * Exit current game and return to idle
     */
    function exitGame(returnToIdle = true) {
        if (currentGame && games[currentGame]) {
            try {
                games[currentGame].destroy();
            } catch (error) {
                console.error('Error destroying game:', error);
            }
        }
        
        currentGame = null;
        isPaused = false;
        clearInactivityTimer();
        
        // Hide game container
        const gameContainer = document.getElementById('game-container');
        if (gameContainer) {
            gameContainer.classList.add('hidden');
            gameContainer.innerHTML = '';
        }
        
        // Hide game selection overlay
        const gameSelection = document.getElementById('game-selection-overlay');
        if (gameSelection) {
            gameSelection.classList.add('hidden');
        }
        
        // Return to idle state using existing UI logic
        if (returnToIdle && typeof updateState === 'function') {
            updateState('IDLE', true);
        }
        
        console.log('Game exited');
    }
    
    /**
     * Pause current game (called when message overlay appears)
     */
    function pauseGame() {
        if (currentGame && games[currentGame] && !isPaused) {
            isPaused = true;
            if (typeof games[currentGame].pause === 'function') {
                games[currentGame].pause();
            }
            clearInactivityTimer();
            console.log('Game paused');
        }
    }
    
    /**
     * Resume current game (called when message overlay is dismissed)
     */
    function resumeGame() {
        if (currentGame && games[currentGame] && isPaused) {
            isPaused = false;
            if (typeof games[currentGame].resume === 'function') {
                games[currentGame].resume();
            }
            resetInactivityTimer();
            console.log('Game resumed');
        }
    }
    
    /**
     * Record user activity (resets inactivity timer)
     */
    function recordActivity() {
        if (currentGame && !isPaused) {
            resetInactivityTimer();
        }
    }
    
    /**
     * Reset the inactivity timer
     */
    function resetInactivityTimer() {
        clearInactivityTimer();
        inactivityTimer = setTimeout(() => {
            console.log('Inactivity timeout - exiting game');
            exitGame(true);
        }, INACTIVITY_TIMEOUT);
    }
    
    /**
     * Clear the inactivity timer
     */
    function clearInactivityTimer() {
        if (inactivityTimer) {
            clearTimeout(inactivityTimer);
            inactivityTimer = null;
        }
    }
    
    /**
     * Check if a game is currently running
     */
    function isGameActive() {
        return currentGame !== null;
    }
    
    /**
     * Check if game is paused
     */
    function isGamePaused() {
        return isPaused;
    }
    
    /**
     * Get current game name
     */
    function getCurrentGame() {
        return currentGame;
    }
    
    /**
     * Show game selection overlay
     */
    function showGameSelection() {
        const overlay = document.getElementById('game-selection-overlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }
    
    /**
     * Hide game selection overlay
     */
    function hideGameSelection() {
        const overlay = document.getElementById('game-selection-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    
    // Public API
    return {
        registerGame,
        startGame,
        exitGame,
        pauseGame,
        resumeGame,
        recordActivity,
        isGameActive,
        isGamePaused,
        getCurrentGame,
        showGameSelection,
        hideGameSelection
    };
})();
