/**
 * Snake Game - Touch-friendly version
 * Relaxed, casual snake game with tea cup collectibles
 */

const SnakeGame = (function() {
    // Game constants
    const GRID_SIZE = 12; // 12x12 grid for large cells on 5" display
    const GAME_SPEED = 280; // Slow, relaxed speed (ms per move)
    
    // Game state
    let canvas = null;
    let ctx = null;
    let cellSize = 0;
    let snake = [];
    let direction = { x: 1, y: 0 };
    let nextDirection = { x: 1, y: 0 };
    let teaCup = { x: 0, y: 0 };
    let score = 0;
    let gameLoop = null;
    let isRunning = false;
    let teaCupImage = null;
    let imageLoaded = false;
    
    // Touch zones (percentages)
    const TOUCH_ZONE = 0.25; // 25% of screen for each direction
    
    /**
     * Initialize the game
     */
    function init() {
        createGameUI();
        loadAssets();
        setupTouchControls();
        resetGame();
    }
    
    /**
     * Create game UI elements
     */
    function createGameUI() {
        const container = document.getElementById('game-container');
        container.innerHTML = `
            <div class="snake-game">
                <div class="snake-header">
                    <button id="snake-exit" class="game-exit-btn">✕</button>
                    <div class="snake-score">🍵 <span id="snake-score-value">0</span></div>
                </div>
                <canvas id="snake-canvas"></canvas>
                <div class="snake-touch-hint">Tap edges to move</div>
                <div id="snake-game-over" class="game-over-overlay hidden">
                    <div class="game-over-content">
                        <h2>Game Over!</h2>
                        <p>Tea cups collected: <span id="snake-final-score">0</span></p>
                        <div class="game-over-buttons">
                            <button id="snake-play-again" class="game-btn">Play Again</button>
                            <button id="snake-exit-game" class="game-btn secondary">Exit</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Setup canvas
        canvas = document.getElementById('snake-canvas');
        ctx = canvas.getContext('2d');
        
        // Size canvas to fit container
        const gameArea = container.querySelector('.snake-game');
        const headerHeight = 60;
        const hintHeight = 40;
        const padding = 20;
        const availableHeight = window.innerHeight - headerHeight - hintHeight - padding;
        const availableWidth = window.innerWidth - padding;
        const size = Math.min(availableWidth, availableHeight);
        
        canvas.width = size;
        canvas.height = size;
        cellSize = Math.floor(size / GRID_SIZE);
        
        // Setup button handlers
        document.getElementById('snake-exit').addEventListener('click', () => {
            GameManager.exitGame(true);
        });
        
        document.getElementById('snake-play-again').addEventListener('click', () => {
            document.getElementById('snake-game-over').classList.add('hidden');
            resetGame();
            start();
        });
        
        document.getElementById('snake-exit-game').addEventListener('click', () => {
            GameManager.exitGame(true);
        });
    }
    
    /**
     * Load game assets
     */
    function loadAssets() {
        teaCupImage = new Image();
        teaCupImage.onload = () => {
            imageLoaded = true;
        };
        teaCupImage.onerror = () => {
            // Try SVG fallback
            if (!teaCupImage.src.includes('.svg')) {
                teaCupImage.src = '../games/assets/snake/tea_cup.svg';
            } else {
                imageLoaded = false;
            }
        };
        teaCupImage.src = '../games/assets/snake/tea_cup.png';
    }
    
    /**
     * Setup touch controls with large zones
     */
    function setupTouchControls() {
        canvas.addEventListener('click', handleTouch);
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches.length > 0) {
                handleTouchEvent(e.touches[0]);
            }
        }, { passive: false });
    }
    
    /**
     * Handle touch/click input
     */
    function handleTouch(e) {
        handleTouchEvent(e);
    }
    
    /**
     * Process touch event and determine direction
     */
    function handleTouchEvent(e) {
        if (!isRunning) return;
        
        GameManager.recordActivity();
        
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        
        let newDir = null;
        
        // Determine direction based on touch zone
        if (y < TOUCH_ZONE) {
            // Top zone - move up
            newDir = { x: 0, y: -1 };
        } else if (y > 1 - TOUCH_ZONE) {
            // Bottom zone - move down
            newDir = { x: 0, y: 1 };
        } else if (x < TOUCH_ZONE) {
            // Left zone - move left
            newDir = { x: -1, y: 0 };
        } else if (x > 1 - TOUCH_ZONE) {
            // Right zone - move right
            newDir = { x: 1, y: 0 };
        }
        
        // Validate direction (can't go opposite)
        if (newDir) {
            const isOpposite = (newDir.x === -direction.x && newDir.x !== 0) ||
                              (newDir.y === -direction.y && newDir.y !== 0);
            if (!isOpposite) {
                nextDirection = newDir;
            }
        }
    }
    
    /**
     * Reset game state
     */
    function resetGame() {
        // Start snake in center
        const startX = Math.floor(GRID_SIZE / 2);
        const startY = Math.floor(GRID_SIZE / 2);
        snake = [
            { x: startX, y: startY },
            { x: startX - 1, y: startY },
            { x: startX - 2, y: startY }
        ];
        
        direction = { x: 1, y: 0 };
        nextDirection = { x: 1, y: 0 };
        score = 0;
        updateScoreDisplay();
        spawnTeaCup();
    }
    
    /**
     * Start the game
     */
    function start() {
        if (isRunning) return;
        isRunning = true;
        gameLoop = setInterval(update, GAME_SPEED);
        draw();
    }
    
    /**
     * Pause the game
     */
    function pause() {
        isRunning = false;
        if (gameLoop) {
            clearInterval(gameLoop);
            gameLoop = null;
        }
    }
    
    /**
     * Resume the game
     */
    function resume() {
        if (!isRunning && snake.length > 0) {
            isRunning = true;
            gameLoop = setInterval(update, GAME_SPEED);
        }
    }
    
    /**
     * Main game update loop
     */
    function update() {
        if (!isRunning) return;
        
        // Apply next direction
        direction = nextDirection;
        
        // Calculate new head position
        const head = { ...snake[0] };
        head.x += direction.x;
        head.y += direction.y;
        
        // Wrap around screen (exit one side, enter from opposite)
        if (head.x < 0) {
            head.x = GRID_SIZE - 1;
        } else if (head.x >= GRID_SIZE) {
            head.x = 0;
        }
        
        if (head.y < 0) {
            head.y = GRID_SIZE - 1;
        } else if (head.y >= GRID_SIZE) {
            head.y = 0;
        }
        
        // Check self collision (snake bites itself)
        for (const segment of snake) {
            if (head.x === segment.x && head.y === segment.y) {
                gameOver();
                return;
            }
        }
        
        // Add new head
        snake.unshift(head);
        
        // Check tea cup collection
        if (head.x === teaCup.x && head.y === teaCup.y) {
            score++;
            updateScoreDisplay();
            spawnTeaCup();
        } else {
            // Remove tail if not eating
            snake.pop();
        }
        
        draw();
    }
    
    /**
     * Spawn tea cup at random position
     */
    function spawnTeaCup() {
        let validPosition = false;
        let attempts = 0;
        
        while (!validPosition && attempts < 100) {
            teaCup.x = Math.floor(Math.random() * GRID_SIZE);
            teaCup.y = Math.floor(Math.random() * GRID_SIZE);
            
            // Check not on snake
            validPosition = !snake.some(s => s.x === teaCup.x && s.y === teaCup.y);
            attempts++;
        }
    }
    
    /**
     * Draw the game
     */
    function draw() {
        // Clear canvas
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid lines (subtle)
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= GRID_SIZE; i++) {
            ctx.beginPath();
            ctx.moveTo(i * cellSize, 0);
            ctx.lineTo(i * cellSize, canvas.height);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, i * cellSize);
            ctx.lineTo(canvas.width, i * cellSize);
            ctx.stroke();
        }
        
        // Draw touch zones (very subtle hints)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.02)';
        // Top zone
        ctx.fillRect(0, 0, canvas.width, canvas.height * TOUCH_ZONE);
        // Bottom zone
        ctx.fillRect(0, canvas.height * (1 - TOUCH_ZONE), canvas.width, canvas.height * TOUCH_ZONE);
        // Left zone
        ctx.fillRect(0, 0, canvas.width * TOUCH_ZONE, canvas.height);
        // Right zone
        ctx.fillRect(canvas.width * (1 - TOUCH_ZONE), 0, canvas.width * TOUCH_ZONE, canvas.height);
        
        // Draw tea cup
        const cupX = teaCup.x * cellSize;
        const cupY = teaCup.y * cellSize;
        const cupPadding = cellSize * 0.1;
        
        if (imageLoaded && teaCupImage.complete) {
            ctx.drawImage(teaCupImage, cupX + cupPadding, cupY + cupPadding, 
                         cellSize - cupPadding * 2, cellSize - cupPadding * 2);
        } else {
            // Fallback: draw a simple tea cup shape
            drawTeaCupFallback(cupX, cupY);
        }
        
        // Draw snake
        snake.forEach((segment, index) => {
            const x = segment.x * cellSize;
            const y = segment.y * cellSize;
            const padding = 2;
            
            if (index === 0) {
                // Head - brighter and with eyes
                ctx.fillStyle = '#4ade80';
                roundRect(ctx, x + padding, y + padding, 
                         cellSize - padding * 2, cellSize - padding * 2, 8);
                ctx.fill();
                
                // Eyes
                ctx.fillStyle = '#fff';
                const eyeSize = cellSize * 0.15;
                const eyeOffset = cellSize * 0.25;
                
                if (direction.x === 1) { // Right
                    ctx.beginPath();
                    ctx.arc(x + cellSize - eyeOffset, y + eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.arc(x + cellSize - eyeOffset, y + cellSize - eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.fill();
                } else if (direction.x === -1) { // Left
                    ctx.beginPath();
                    ctx.arc(x + eyeOffset, y + eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.arc(x + eyeOffset, y + cellSize - eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.fill();
                } else if (direction.y === -1) { // Up
                    ctx.beginPath();
                    ctx.arc(x + eyeOffset, y + eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.arc(x + cellSize - eyeOffset, y + eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.fill();
                } else { // Down
                    ctx.beginPath();
                    ctx.arc(x + eyeOffset, y + cellSize - eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.arc(x + cellSize - eyeOffset, y + cellSize - eyeOffset, eyeSize, 0, Math.PI * 2);
                    ctx.fill();
                }
            } else {
                // Body - gradient from green to teal
                const colorIntensity = 1 - (index / snake.length) * 0.4;
                ctx.fillStyle = `rgba(74, 222, 128, ${colorIntensity})`;
                roundRect(ctx, x + padding, y + padding, 
                         cellSize - padding * 2, cellSize - padding * 2, 6);
                ctx.fill();
            }
        });
    }
    
    /**
     * Draw fallback tea cup when image not available
     */
    function drawTeaCupFallback(x, y) {
        const padding = cellSize * 0.15;
        const cupWidth = cellSize - padding * 2;
        const cupHeight = cellSize * 0.6;
        const cupX = x + padding;
        const cupY = y + cellSize - padding - cupHeight;
        
        // Cup body
        ctx.fillStyle = '#f5f5dc';
        ctx.beginPath();
        ctx.moveTo(cupX, cupY);
        ctx.lineTo(cupX + cupWidth * 0.1, cupY + cupHeight);
        ctx.lineTo(cupX + cupWidth * 0.9, cupY + cupHeight);
        ctx.lineTo(cupX + cupWidth, cupY);
        ctx.closePath();
        ctx.fill();
        
        // Handle
        ctx.strokeStyle = '#f5f5dc';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(cupX + cupWidth + 5, cupY + cupHeight * 0.5, 8, -Math.PI * 0.5, Math.PI * 0.5);
        ctx.stroke();
        
        // Steam
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 2;
        for (let i = 0; i < 2; i++) {
            const steamX = cupX + cupWidth * 0.3 + i * cupWidth * 0.4;
            ctx.beginPath();
            ctx.moveTo(steamX, cupY - 2);
            ctx.quadraticCurveTo(steamX + 5, cupY - 10, steamX, cupY - 15);
            ctx.stroke();
        }
    }
    
    /**
     * Helper: Draw rounded rectangle
     */
    function roundRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }
    
    /**
     * Update score display
     */
    function updateScoreDisplay() {
        const scoreEl = document.getElementById('snake-score-value');
        if (scoreEl) {
            scoreEl.textContent = score;
        }
    }
    
    /**
     * Game over
     */
    function gameOver() {
        pause();
        
        document.getElementById('snake-final-score').textContent = score;
        document.getElementById('snake-game-over').classList.remove('hidden');
        
        // Auto-exit after 15 seconds if no interaction
        setTimeout(() => {
            if (!isRunning && document.getElementById('snake-game-over') && 
                !document.getElementById('snake-game-over').classList.contains('hidden')) {
                GameManager.exitGame(true);
            }
        }, 15000);
    }
    
    /**
     * Destroy the game
     */
    function destroy() {
        pause();
        canvas = null;
        ctx = null;
        snake = [];
        isRunning = false;
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
    GameManager.registerGame('snake', SnakeGame);
}
