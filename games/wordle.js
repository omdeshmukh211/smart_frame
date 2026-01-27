/**
 * Wordle Game - Daily Word Puzzle
 * Touch-optimized, calm and ambient
 */

const WordleGame = (function() {
    // Game constants
    const WORD_LENGTH = 5;
    const MAX_ATTEMPTS = 6;
    const RESULT_DISPLAY_TIME = 10000; // 10 seconds before auto-exit
    const INACTIVITY_TIMEOUT = 120000; // 120 seconds
    
    // Word list (common 5-letter words)
    const WORD_LIST = [
        'APPLE', 'BEACH', 'BRAIN', 'BREAD', 'BRING', 'BRUSH', 'BUILD', 'CANDY',
        'CHAIR', 'CHASE', 'CHEST', 'CHILD', 'CLEAN', 'CLEAR', 'CLIMB', 'CLOSE',
        'CLOUD', 'COACH', 'COAST', 'CORAL', 'CRANE', 'CREAM', 'DANCE', 'DREAM',
        'DRINK', 'EARTH', 'EMBER', 'ENJOY', 'FLAME', 'FLASH', 'FLOOR', 'FLOWN',
        'FOCUS', 'FORGE', 'FRESH', 'FRUIT', 'GIANT', 'GRACE', 'GRAIN', 'GRAPE',
        'GRASS', 'GREEN', 'GROVE', 'GUARD', 'GUESS', 'HAPPY', 'HEART', 'HONEY',
        'HORSE', 'HOUSE', 'HUMAN', 'JUICE', 'KNOWN', 'LEMON', 'LIGHT', 'LUCKY',
        'LUNAR', 'MAPLE', 'MEDAL', 'MELON', 'MIGHT', 'MISTY', 'MONEY', 'MONTH',
        'NIGHT', 'NOBLE', 'OCEAN', 'OLIVE', 'PAINT', 'PAPER', 'PEACE', 'PEACH',
        'PEARL', 'PIANO', 'PILOT', 'PLACE', 'PLAIN', 'PLANT', 'PLATE', 'PLAZA',
        'PLUME', 'POINT', 'POLAR', 'POWER', 'PRIDE', 'PRIZE', 'PROOF', 'QUIET',
        'RADIO', 'RAINY', 'RAPID', 'REACH', 'REALM', 'RIVER', 'ROBIN', 'ROYAL',
        'SHORE', 'SHINE', 'SIGHT', 'SILLY', 'SKATE', 'SLEEP', 'SLICE', 'SLIDE',
        'SMILE', 'SMOKE', 'SNOWY', 'SOLAR', 'SOUND', 'SOUTH', 'SPACE', 'SPARE',
        'SPEAK', 'SPEND', 'SPICE', 'SPINE', 'SPOKE', 'SPORT', 'STAMP', 'STAND',
        'STARK', 'START', 'STEAM', 'STEEL', 'STEEP', 'STERN', 'STILL', 'STOCK',
        'STONE', 'STORE', 'STORM', 'STORY', 'STOVE', 'STUDY', 'STYLE', 'SUGAR',
        'SUNNY', 'SUPER', 'SWEET', 'SWIFT', 'SWING', 'TABLE', 'TASTE', 'TEACH',
        'TIDAL', 'TIGER', 'TIMER', 'TOAST', 'TODAY', 'TOKEN', 'TOPIC', 'TORCH',
        'TOTAL', 'TOUCH', 'TOWER', 'TRACE', 'TRACK', 'TRADE', 'TRAIL', 'TRAIN',
        'TREAT', 'TREND', 'TRIAL', 'TRIBE', 'TRIED', 'TROUT', 'TRULY', 'TRUNK',
        'TRUST', 'TRUTH', 'TULIP', 'UNCLE', 'UNITY', 'URBAN', 'USUAL', 'VALID',
        'VALUE', 'VAPOR', 'VAULT', 'VIDEO', 'VIGOR', 'VIOLA', 'VIRAL', 'VISIT',
        'VITAL', 'VIVID', 'VOCAL', 'VOICE', 'WATCH', 'WATER', 'WHEAT', 'WHEEL',
        'WHITE', 'WHOLE', 'WORLD', 'WORTH', 'WOULD', 'WOUND', 'WRITE', 'YOUNG'
    ];
    
    // Keyboard layout
    const KEYBOARD_ROWS = [
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫']
    ];
    
    // Game state
    let targetWord = '';
    let currentAttempt = 0;
    let currentGuess = '';
    let attempts = [];
    let gameOver = false;
    let gameWon = false;
    let letterStates = {}; // Track letter colors for keyboard
    let autoExitTimer = null;
    let inactivityTimer = null;
    let isPaused = false;
    
    // Storage keys
    const STORAGE_KEY = 'wordle_daily';
    
    /**
     * Get today's date string
     */
    function getTodayString() {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    }
    
    /**
     * Get daily word based on date
     */
    function getDailyWord() {
        const today = getTodayString();
        // Use date to seed word selection (deterministic)
        const dateNum = today.split('-').join('');
        const index = parseInt(dateNum) % WORD_LIST.length;
        return WORD_LIST[index];
    }
    
    /**
     * Load saved game state from localStorage
     */
    function loadGameState() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const state = JSON.parse(saved);
                if (state.date === getTodayString()) {
                    return state;
                }
            }
        } catch (e) {
            console.warn('Could not load Wordle state:', e);
        }
        return null;
    }
    
    /**
     * Save game state to localStorage
     */
    function saveGameState() {
        try {
            const state = {
                date: getTodayString(),
                targetWord: targetWord,
                attempts: attempts,
                gameOver: gameOver,
                gameWon: gameWon,
                letterStates: letterStates
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
            console.warn('Could not save Wordle state:', e);
        }
    }
    
    /**
     * Initialize the game
     */
    function init() {
        createGameUI();
        
        // Try to load existing game for today
        const savedState = loadGameState();
        if (savedState) {
            targetWord = savedState.targetWord;
            attempts = savedState.attempts;
            gameOver = savedState.gameOver;
            gameWon = savedState.gameWon;
            letterStates = savedState.letterStates || {};
            currentAttempt = attempts.length;
            currentGuess = '';
            
            // Restore the grid
            restoreGrid();
            updateKeyboard();
            
            // If game was already complete, show result
            if (gameOver) {
                setTimeout(() => showResult(), 500);
            }
        } else {
            // New game for today
            targetWord = getDailyWord();
            attempts = [];
            currentAttempt = 0;
            currentGuess = '';
            gameOver = false;
            gameWon = false;
            letterStates = {};
        }
        
        isPaused = false;
        resetInactivityTimer();
    }
    
    /**
     * Create game UI elements
     */
    function createGameUI() {
        const container = document.getElementById('game-container');
        container.innerHTML = `
            <div class="wordle-game">
                <div class="wordle-header">
                    <button id="wordle-exit" class="game-exit-btn">✕</button>
                    <div class="wordle-title">Daily Wordle</div>
                    <div class="wordle-spacer"></div>
                </div>
                
                <div class="wordle-grid-container">
                    <div class="wordle-grid" id="wordle-grid">
                        ${createGridHTML()}
                    </div>
                </div>
                
                <div class="wordle-keyboard" id="wordle-keyboard">
                    ${createKeyboardHTML()}
                </div>
                
                <div id="wordle-result" class="game-over-overlay hidden">
                    <div class="game-over-content wordle-result-content">
                        <h2 id="wordle-result-text">Well done!</h2>
                        <p id="wordle-result-word" class="wordle-result-word"></p>
                        <div class="game-over-buttons">
                            <button id="wordle-exit-game" class="game-btn">Exit</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Setup event listeners
        document.getElementById('wordle-exit').addEventListener('click', () => {
            clearTimers();
            GameManager.exitGame(true);
        });
        
        document.getElementById('wordle-exit-game').addEventListener('click', () => {
            clearTimers();
            GameManager.exitGame(true);
        });
        
        // Keyboard event listeners
        setupKeyboardListeners();
    }
    
    /**
     * Create grid HTML
     */
    function createGridHTML() {
        let html = '';
        for (let row = 0; row < MAX_ATTEMPTS; row++) {
            html += '<div class="wordle-row">';
            for (let col = 0; col < WORD_LENGTH; col++) {
                html += `<div class="wordle-tile" id="tile-${row}-${col}"></div>`;
            }
            html += '</div>';
        }
        return html;
    }
    
    /**
     * Create keyboard HTML
     */
    function createKeyboardHTML() {
        let html = '';
        KEYBOARD_ROWS.forEach((row, rowIndex) => {
            html += `<div class="wordle-keyboard-row">`;
            row.forEach(key => {
                const isWide = key === 'ENTER' || key === '⌫';
                const keyClass = isWide ? 'wordle-key wide' : 'wordle-key';
                const keyId = key === '⌫' ? 'BACKSPACE' : key;
                html += `<button class="${keyClass}" data-key="${keyId}">${key}</button>`;
            });
            html += '</div>';
        });
        return html;
    }
    
    /**
     * Setup keyboard click/touch listeners
     */
    function setupKeyboardListeners() {
        const keyboard = document.getElementById('wordle-keyboard');
        
        keyboard.addEventListener('click', (e) => {
            if (isPaused || gameOver) return;
            
            const key = e.target.closest('.wordle-key');
            if (key) {
                handleKeyPress(key.dataset.key);
                recordActivity();
            }
        });
        
        keyboard.addEventListener('touchstart', (e) => {
            if (isPaused || gameOver) return;
            
            const key = e.target.closest('.wordle-key');
            if (key) {
                e.preventDefault();
                key.classList.add('pressed');
            }
        }, { passive: false });
        
        keyboard.addEventListener('touchend', (e) => {
            const key = e.target.closest('.wordle-key');
            if (key) {
                key.classList.remove('pressed');
            }
        });
    }
    
    /**
     * Handle key press
     */
    function handleKeyPress(key) {
        if (gameOver || isPaused) return;
        
        if (key === 'ENTER') {
            submitGuess();
        } else if (key === 'BACKSPACE') {
            deleteLetter();
        } else if (key.length === 1 && key >= 'A' && key <= 'Z') {
            addLetter(key);
        }
    }
    
    /**
     * Add a letter to current guess
     */
    function addLetter(letter) {
        if (currentGuess.length < WORD_LENGTH) {
            currentGuess += letter;
            updateCurrentRow();
        }
    }
    
    /**
     * Delete last letter
     */
    function deleteLetter() {
        if (currentGuess.length > 0) {
            currentGuess = currentGuess.slice(0, -1);
            updateCurrentRow();
        }
    }
    
    /**
     * Update current row display
     */
    function updateCurrentRow() {
        for (let col = 0; col < WORD_LENGTH; col++) {
            const tile = document.getElementById(`tile-${currentAttempt}-${col}`);
            if (tile) {
                tile.textContent = currentGuess[col] || '';
                tile.className = 'wordle-tile' + (currentGuess[col] ? ' filled' : '');
            }
        }
    }
    
    /**
     * Submit current guess
     */
    function submitGuess() {
        if (currentGuess.length !== WORD_LENGTH) {
            shakeCurrentRow();
            return;
        }
        
        // Check if word is in list (optional - allow any 5 letters for casual play)
        const guess = currentGuess.toUpperCase();
        
        // Evaluate guess
        const result = evaluateGuess(guess);
        
        // Store attempt
        attempts.push({ word: guess, result: result });
        
        // Animate tiles
        revealTiles(currentAttempt, guess, result);
        
        // Update letter states for keyboard
        for (let i = 0; i < guess.length; i++) {
            const letter = guess[i];
            const state = result[i];
            
            // Only upgrade state (gray -> yellow -> green)
            if (!letterStates[letter] || 
                (letterStates[letter] === 'absent' && state !== 'absent') ||
                (letterStates[letter] === 'present' && state === 'correct')) {
                letterStates[letter] = state;
            }
        }
        
        // Check win/lose
        if (guess === targetWord) {
            gameWon = true;
            gameOver = true;
            setTimeout(() => showResult(), 1500);
        } else if (currentAttempt >= MAX_ATTEMPTS - 1) {
            gameOver = true;
            setTimeout(() => showResult(), 1500);
        } else {
            currentAttempt++;
            currentGuess = '';
        }
        
        // Save state
        saveGameState();
        
        // Update keyboard colors after animation
        setTimeout(() => updateKeyboard(), 1500);
    }
    
    /**
     * Evaluate guess against target
     */
    function evaluateGuess(guess) {
        const result = Array(WORD_LENGTH).fill('absent');
        const targetLetters = targetWord.split('');
        const guessLetters = guess.split('');
        
        // First pass: find correct positions
        for (let i = 0; i < WORD_LENGTH; i++) {
            if (guessLetters[i] === targetLetters[i]) {
                result[i] = 'correct';
                targetLetters[i] = null;
                guessLetters[i] = null;
            }
        }
        
        // Second pass: find present letters
        for (let i = 0; i < WORD_LENGTH; i++) {
            if (guessLetters[i] !== null) {
                const idx = targetLetters.indexOf(guessLetters[i]);
                if (idx !== -1) {
                    result[i] = 'present';
                    targetLetters[idx] = null;
                }
            }
        }
        
        return result;
    }
    
    /**
     * Reveal tiles with animation
     */
    function revealTiles(row, guess, result) {
        for (let col = 0; col < WORD_LENGTH; col++) {
            const tile = document.getElementById(`tile-${row}-${col}`);
            if (tile) {
                setTimeout(() => {
                    tile.classList.add('flip');
                    setTimeout(() => {
                        tile.classList.add(result[col]);
                        tile.classList.remove('flip');
                        tile.classList.add('revealed');
                    }, 250);
                }, col * 200);
            }
        }
    }
    
    /**
     * Shake current row (invalid input)
     */
    function shakeCurrentRow() {
        const row = document.querySelector(`#wordle-grid .wordle-row:nth-child(${currentAttempt + 1})`);
        if (row) {
            row.classList.add('shake');
            setTimeout(() => row.classList.remove('shake'), 500);
        }
    }
    
    /**
     * Update keyboard colors
     */
    function updateKeyboard() {
        const keys = document.querySelectorAll('.wordle-key');
        keys.forEach(key => {
            const letter = key.dataset.key;
            if (letterStates[letter]) {
                key.classList.remove('correct', 'present', 'absent');
                key.classList.add(letterStates[letter]);
            }
        });
    }
    
    /**
     * Restore grid from saved state
     */
    function restoreGrid() {
        attempts.forEach((attempt, row) => {
            for (let col = 0; col < WORD_LENGTH; col++) {
                const tile = document.getElementById(`tile-${row}-${col}`);
                if (tile) {
                    tile.textContent = attempt.word[col];
                    tile.className = `wordle-tile revealed ${attempt.result[col]}`;
                }
            }
        });
    }
    
    /**
     * Show game result
     */
    function showResult() {
        let resultText = '';
        let wordText = '';
        
        if (gameWon) {
            const messages = [
                '✨ Brilliant!',
                '🌟 Well done!',
                '🎯 Perfect!',
                '💫 Amazing!',
                '🌸 Lovely!',
                '🍀 Lucky guess!'
            ];
            resultText = messages[Math.min(currentAttempt, messages.length - 1)];
        } else {
            resultText = 'Maybe tomorrow';
            wordText = `The word was: ${targetWord}`;
        }
        
        document.getElementById('wordle-result-text').textContent = resultText;
        document.getElementById('wordle-result-word').textContent = wordText;
        document.getElementById('wordle-result').classList.remove('hidden');
        
        // Auto-exit timer
        autoExitTimer = setTimeout(() => {
            GameManager.exitGame(true);
        }, RESULT_DISPLAY_TIME);
    }
    
    /**
     * Record activity (reset inactivity timer)
     */
    function recordActivity() {
        if (typeof GameManager !== 'undefined') {
            GameManager.recordActivity();
        }
        resetInactivityTimer();
    }
    
    /**
     * Reset inactivity timer
     */
    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            if (!gameOver && !isPaused) {
                GameManager.exitGame(true);
            }
        }, INACTIVITY_TIMEOUT);
    }
    
    /**
     * Clear all timers
     */
    function clearTimers() {
        if (autoExitTimer) {
            clearTimeout(autoExitTimer);
            autoExitTimer = null;
        }
        if (inactivityTimer) {
            clearTimeout(inactivityTimer);
            inactivityTimer = null;
        }
    }
    
    /**
     * Start the game
     */
    function start() {
        resetInactivityTimer();
    }
    
    /**
     * Pause the game
     */
    function pause() {
        isPaused = true;
        clearTimers();
    }
    
    /**
     * Resume the game
     */
    function resume() {
        isPaused = false;
        resetInactivityTimer();
    }
    
    /**
     * Destroy the game
     */
    function destroy() {
        clearTimers();
        gameOver = false;
        gameWon = false;
        currentGuess = '';
        attempts = [];
        letterStates = {};
    }
    
    // Public API
    return {
        init,
        start,
        pause,
        resume,
        destroy
    };
})();

// Register with GameManager when loaded
if (typeof GameManager !== 'undefined') {
    GameManager.registerGame('wordle', WordleGame);
}
