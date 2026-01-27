/**
 * Tic Tac Toe Game - Player vs AI or 2 Player
 * Touch-friendly with large tap areas
 */

const TicTacToeGame = (function() {
    // Game constants
    const BOARD_SIZE = 3;
    const RESULT_DISPLAY_TIME = 10000; // 10 seconds before auto-exit
    
    // Game state
    let board = [];
    let currentPlayer = 'X';
    let gameOver = false;
    let winner = null;
    let winningLine = null;
    let canvas = null;
    let ctx = null;
    let cellSize = 0;
    let autoExitTimer = null;
    let gameMode = '1p'; // '1p' for vs AI, '2p' for 2 players
    
    /**
     * Initialize the game
     * @param {Object} options - Game options
     * @param {string} options.mode - '1p' for vs AI, '2p' for 2 players
     */
    function init(options = {}) {
        gameMode = options.mode || '1p';
        createGameUI();
        setupTouchControls();
        resetGame();
    }
    
    /**
     * Create game UI elements
     */
    function createGameUI() {
        const container = document.getElementById('game-container');
        container.innerHTML = `
            <div class="tictactoe-game">
                <div class="tictactoe-header">
                    <button id="tictactoe-exit" class="game-exit-btn">✕</button>
                    <div class="tictactoe-status" id="tictactoe-status"></div>
                </div>
                <canvas id="tictactoe-canvas"></canvas>
                <div id="tictactoe-result" class="game-over-overlay hidden">
                    <div class="game-over-content">
                        <h2 id="tictactoe-result-text">Game Over!</h2>
                        <div class="game-over-buttons">
                            <button id="tictactoe-play-again" class="game-btn">Play Again</button>
                            <button id="tictactoe-exit-game" class="game-btn secondary">Exit</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Setup canvas
        canvas = document.getElementById('tictactoe-canvas');
        ctx = canvas.getContext('2d');
        
        // Size canvas
        const padding = 40;
        const size = Math.min(window.innerWidth - padding, window.innerHeight - 150);
        canvas.width = size;
        canvas.height = size;
        cellSize = size / BOARD_SIZE;
        
        // Setup button handlers
        document.getElementById('tictactoe-exit').addEventListener('click', () => {
            clearAutoExitTimer();
            GameManager.exitGame(true);
        });
        
        document.getElementById('tictactoe-play-again').addEventListener('click', () => {
            clearAutoExitTimer();
            document.getElementById('tictactoe-result').classList.add('hidden');
            resetGame();
            draw();
        });
        
        document.getElementById('tictactoe-exit-game').addEventListener('click', () => {
            clearAutoExitTimer();
            GameManager.exitGame(true);
        });
    }
    
    /**
     * Setup touch controls
     */
    function setupTouchControls() {
        canvas.addEventListener('click', handleClick);
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches.length > 0) {
                handleTouchEvent(e.touches[0]);
            }
        }, { passive: false });
    }
    
    /**
     * Handle click event
     */
    function handleClick(e) {
        handleTouchEvent(e);
    }
    
    /**
     * Process touch/click event
     */
    function handleTouchEvent(e) {
        if (gameOver) return;
        
        // In 1-player mode, only allow moves when it's player's turn (X)
        if (gameMode === '1p' && currentPlayer !== 'X') return;
        
        GameManager.recordActivity();
        
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const col = Math.floor(x / cellSize);
        const row = Math.floor(y / cellSize);
        
        if (row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE) {
            if (board[row][col] === '') {
                makeMove(row, col, currentPlayer);
                
                if (!gameOver && gameMode === '1p' && currentPlayer === 'O') {
                    // AI's turn after a short delay
                    updateStatus("AI thinking...");
                    setTimeout(aiMove, 500);
                }
            }
        }
    }
    
    /**
     * Reset game state
     */
    function resetGame() {
        board = [
            ['', '', ''],
            ['', '', ''],
            ['', '', '']
        ];
        currentPlayer = 'X';
        gameOver = false;
        winner = null;
        winningLine = null;
        clearAutoExitTimer();
        updateTurnStatus();
        draw();
    }
    
    /**
     * Start the game
     */
    function start() {
        draw();
    }
    
    /**
     * Pause the game
     */
    function pause() {
        clearAutoExitTimer();
    }
    
    /**
     * Resume the game
     */
    function resume() {
        draw();
    }
    
    /**
     * Make a move
     */
    function makeMove(row, col, player) {
        board[row][col] = player;
        draw();
        
        // Check for winner
        const result = checkWinner();
        if (result) {
            gameOver = true;
            winner = result.winner;
            winningLine = result.line;
            showResult();
        } else if (isBoardFull()) {
            gameOver = true;
            winner = 'draw';
            showResult();
        } else {
            currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
            updateTurnStatus();
        }
    }
    
    /**
     * AI move - simple and beatable
     */
    function aiMove() {
        if (gameOver) return;
        
        // Strategy: Try to win, then block, then random
        let move = findWinningMove('O');
        if (!move) {
            move = findWinningMove('X'); // Block player
        }
        if (!move) {
            move = findRandomMove();
        }
        
        if (move) {
            makeMove(move.row, move.col, 'O');
        }
    }
    
    /**
     * Find a winning move for a player
     */
    function findWinningMove(player) {
        for (let row = 0; row < BOARD_SIZE; row++) {
            for (let col = 0; col < BOARD_SIZE; col++) {
                if (board[row][col] === '') {
                    // Try this move
                    board[row][col] = player;
                    const result = checkWinner();
                    board[row][col] = '';
                    
                    if (result && result.winner === player) {
                        return { row, col };
                    }
                }
            }
        }
        return null;
    }
    
    /**
     * Find a random valid move
     */
    function findRandomMove() {
        const emptyCells = [];
        for (let row = 0; row < BOARD_SIZE; row++) {
            for (let col = 0; col < BOARD_SIZE; col++) {
                if (board[row][col] === '') {
                    emptyCells.push({ row, col });
                }
            }
        }
        
        if (emptyCells.length > 0) {
            // Prefer center, then corners, then edges
            const center = emptyCells.find(c => c.row === 1 && c.col === 1);
            if (center) return center;
            
            const corners = emptyCells.filter(c => 
                (c.row === 0 || c.row === 2) && (c.col === 0 || c.col === 2)
            );
            if (corners.length > 0) {
                return corners[Math.floor(Math.random() * corners.length)];
            }
            
            return emptyCells[Math.floor(Math.random() * emptyCells.length)];
        }
        return null;
    }
    
    /**
     * Check for a winner
     */
    function checkWinner() {
        // Check rows
        for (let row = 0; row < BOARD_SIZE; row++) {
            if (board[row][0] !== '' && 
                board[row][0] === board[row][1] && 
                board[row][1] === board[row][2]) {
                return {
                    winner: board[row][0],
                    line: [{ row, col: 0 }, { row, col: 1 }, { row, col: 2 }]
                };
            }
        }
        
        // Check columns
        for (let col = 0; col < BOARD_SIZE; col++) {
            if (board[0][col] !== '' && 
                board[0][col] === board[1][col] && 
                board[1][col] === board[2][col]) {
                return {
                    winner: board[0][col],
                    line: [{ row: 0, col }, { row: 1, col }, { row: 2, col }]
                };
            }
        }
        
        // Check diagonals
        if (board[0][0] !== '' && 
            board[0][0] === board[1][1] && 
            board[1][1] === board[2][2]) {
            return {
                winner: board[0][0],
                line: [{ row: 0, col: 0 }, { row: 1, col: 1 }, { row: 2, col: 2 }]
            };
        }
        
        if (board[0][2] !== '' && 
            board[0][2] === board[1][1] && 
            board[1][1] === board[2][0]) {
            return {
                winner: board[0][2],
                line: [{ row: 0, col: 2 }, { row: 1, col: 1 }, { row: 2, col: 0 }]
            };
        }
        
        return null;
    }
    
    /**
     * Check if board is full
     */
    function isBoardFull() {
        for (let row = 0; row < BOARD_SIZE; row++) {
            for (let col = 0; col < BOARD_SIZE; col++) {
                if (board[row][col] === '') return false;
            }
        }
        return true;
    }
    
    /**
     * Draw the game board
     */
    function draw() {
        const lineWidth = 8;
        const symbolPadding = cellSize * 0.2;
        const symbolLineWidth = 12;
        
        // Clear canvas
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid lines
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        
        // Vertical lines
        for (let i = 1; i < BOARD_SIZE; i++) {
            ctx.beginPath();
            ctx.moveTo(i * cellSize, symbolPadding);
            ctx.lineTo(i * cellSize, canvas.height - symbolPadding);
            ctx.stroke();
        }
        
        // Horizontal lines
        for (let i = 1; i < BOARD_SIZE; i++) {
            ctx.beginPath();
            ctx.moveTo(symbolPadding, i * cellSize);
            ctx.lineTo(canvas.width - symbolPadding, i * cellSize);
            ctx.stroke();
        }
        
        // Draw X's and O's
        for (let row = 0; row < BOARD_SIZE; row++) {
            for (let col = 0; col < BOARD_SIZE; col++) {
                const centerX = col * cellSize + cellSize / 2;
                const centerY = row * cellSize + cellSize / 2;
                const size = cellSize / 2 - symbolPadding;
                
                // Highlight winning cells
                const isWinningCell = winningLine && 
                    winningLine.some(c => c.row === row && c.col === col);
                
                if (board[row][col] === 'X') {
                    ctx.strokeStyle = isWinningCell ? '#4ade80' : '#ef4444';
                    ctx.lineWidth = symbolLineWidth;
                    ctx.lineCap = 'round';
                    
                    ctx.beginPath();
                    ctx.moveTo(centerX - size, centerY - size);
                    ctx.lineTo(centerX + size, centerY + size);
                    ctx.stroke();
                    
                    ctx.beginPath();
                    ctx.moveTo(centerX + size, centerY - size);
                    ctx.lineTo(centerX - size, centerY + size);
                    ctx.stroke();
                    
                } else if (board[row][col] === 'O') {
                    ctx.strokeStyle = isWinningCell ? '#4ade80' : '#3b82f6';
                    ctx.lineWidth = symbolLineWidth;
                    
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, size, 0, Math.PI * 2);
                    ctx.stroke();
                }
            }
        }
        
        // Draw winning line
        if (winningLine && winningLine.length === 3) {
            ctx.strokeStyle = '#4ade80';
            ctx.lineWidth = 6;
            ctx.lineCap = 'round';
            
            const start = winningLine[0];
            const end = winningLine[2];
            
            const startX = start.col * cellSize + cellSize / 2;
            const startY = start.row * cellSize + cellSize / 2;
            const endX = end.col * cellSize + cellSize / 2;
            const endY = end.row * cellSize + cellSize / 2;
            
            ctx.beginPath();
            ctx.moveTo(startX, startY);
            ctx.lineTo(endX, endY);
            ctx.stroke();
        }
    }
    
    /**
     * Update status text
     */
    function updateStatus(text) {
        const statusEl = document.getElementById('tictactoe-status');
        if (statusEl) {
            statusEl.textContent = text;
        }
    }
    
    /**
     * Update turn status based on game mode
     */
    function updateTurnStatus() {
        if (gameMode === '2p') {
            const playerName = currentPlayer === 'X' ? 'Player 1' : 'Player 2';
            updateStatus(`${playerName}'s turn (${currentPlayer})`);
        } else {
            if (currentPlayer === 'X') {
                updateStatus("Your turn (X)");
            } else {
                updateStatus("AI thinking...");
            }
        }
    }
    
    /**
     * Show game result
     */
    function showResult() {
        draw(); // Redraw to show winning line
        
        let resultText = '';
        if (gameMode === '2p') {
            // 2-player mode results
            if (winner === 'X') {
                resultText = '🎉 Player 1 Wins!';
            } else if (winner === 'O') {
                resultText = '🎉 Player 2 Wins!';
            } else {
                resultText = "🤝 It's a Draw!";
            }
        } else {
            // 1-player mode results
            if (winner === 'X') {
                resultText = '🎉 You Win!';
            } else if (winner === 'O') {
                resultText = '🤖 AI Wins!';
            } else {
                resultText = "🤝 It's a Draw!";
            }
        }
        
        document.getElementById('tictactoe-result-text').textContent = resultText;
        document.getElementById('tictactoe-result').classList.remove('hidden');
        
        // Auto-exit timer
        autoExitTimer = setTimeout(() => {
            GameManager.exitGame(true);
        }, RESULT_DISPLAY_TIME);
    }
    
    /**
     * Clear auto-exit timer
     */
    function clearAutoExitTimer() {
        if (autoExitTimer) {
            clearTimeout(autoExitTimer);
            autoExitTimer = null;
        }
    }
    
    /**
     * Destroy the game
     */
    function destroy() {
        clearAutoExitTimer();
        canvas = null;
        ctx = null;
        board = [];
        gameOver = false;
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
    GameManager.registerGame('tictactoe', TicTacToeGame);
}
