/**
 * Snake Game Embed - A simple snake game that can be embedded in an iframe
 */

// Snake game implementation for preview
class SnakeGameEmbed {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.gridSize = 20;
        this.tileCount = 20;
        this.tileSize = this.canvas.width / this.tileCount;
        
        // Initial snake position and velocity
        this.snake = [
            { x: 10, y: 10 }
        ];
        this.velocityX = 0;
        this.velocityY = 0;
        
        // Food position
        this.food = {
            x: Math.floor(Math.random() * this.tileCount),
            y: Math.floor(Math.random() * this.tileCount)
        };
        
        // Game state
        this.gameOver = false;
        this.score = 0;
        
        // Bind event handlers
        this.handleKeyDown = this.handleKeyDown.bind(this);
        document.addEventListener('keydown', this.handleKeyDown);
        
        // Start game loop
        this.gameInterval = setInterval(() => this.gameLoop(), 100);
    }
    
    gameLoop() {
        if (this.gameOver) return;
        
        // Move snake
        this.moveSnake();
        
        // Check collisions
        this.checkCollisions();
        
        // Draw everything
        this.draw();
    }
    
    moveSnake() {
        // Create new head based on velocity
        const head = { 
            x: this.snake[0].x + this.velocityX, 
            y: this.snake[0].y + this.velocityY 
        };
        
        // Add new head to beginning of snake array
        this.snake.unshift(head);
        
        // Check if snake ate food
        if (head.x === this.food.x && head.y === this.food.y) {
            // Increase score
            this.score++;
            
            // Generate new food
            this.food = {
                x: Math.floor(Math.random() * this.tileCount),
                y: Math.floor(Math.random() * this.tileCount)
            };
        } else {
            // Remove tail if snake didn't eat food
            this.snake.pop();
        }
    }
    
    checkCollisions() {
        const head = this.snake[0];
        
        // Check wall collisions
        if (head.x < 0 || head.x >= this.tileCount || head.y < 0 || head.y >= this.tileCount) {
            this.gameOver = true;
        }
        
        // Check self collisions (starting from 1 to skip the head)
        for (let i = 1; i < this.snake.length; i++) {
            if (head.x === this.snake[i].x && head.y === this.snake[i].y) {
                this.gameOver = true;
                break;
            }
        }
    }
    
    draw() {
        // Clear canvas
        this.ctx.fillStyle = '#f0f0f0';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw snake
        this.ctx.fillStyle = '#4CAF50';
        for (const segment of this.snake) {
            this.ctx.fillRect(
                segment.x * this.tileSize,
                segment.y * this.tileSize,
                this.tileSize - 2,
                this.tileSize - 2
            );
        }
        
        // Draw food
        this.ctx.fillStyle = '#FF5252';
        this.ctx.fillRect(
            this.food.x * this.tileSize,
            this.food.y * this.tileSize,
            this.tileSize - 2,
            this.tileSize - 2
        );
        
        // Draw score
        this.ctx.fillStyle = '#333';
        this.ctx.font = '20px Arial';
        this.ctx.fillText(`Score: ${this.score}`, 10, 30);
        
        // Draw game over message
        if (this.gameOver) {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#fff';
            this.ctx.font = 'bold 30px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Game Over!', this.canvas.width / 2, this.canvas.height / 2 - 15);
            
            this.ctx.font = '20px Arial';
            this.ctx.fillText(`Score: ${this.score}`, this.canvas.width / 2, this.canvas.height / 2 + 15);
            
            this.ctx.font = '16px Arial';
            this.ctx.fillText('Press R to restart', this.canvas.width / 2, this.canvas.height / 2 + 45);
        }
    }
    
    handleKeyDown(e) {
        // Restart game if game over
        if (this.gameOver && e.key === 'r') {
            this.restart();
            return;
        }
        
        // Change direction based on arrow keys
        switch (e.key) {
            case 'ArrowUp':
                if (this.velocityY !== 1) { // Prevent moving directly opposite current direction
                    this.velocityX = 0;
                    this.velocityY = -1;
                }
                break;
            case 'ArrowDown':
                if (this.velocityY !== -1) {
                    this.velocityX = 0;
                    this.velocityY = 1;
                }
                break;
            case 'ArrowLeft':
                if (this.velocityX !== 1) {
                    this.velocityX = -1;
                    this.velocityY = 0;
                }
                break;
            case 'ArrowRight':
                if (this.velocityX !== -1) {
                    this.velocityX = 1;
                    this.velocityY = 0;
                }
                break;
        }
    }
    
    restart() {
        // Reset snake
        this.snake = [{ x: 10, y: 10 }];
        this.velocityX = 0;
        this.velocityY = 0;
        
        // Reset food
        this.food = {
            x: Math.floor(Math.random() * this.tileCount),
            y: Math.floor(Math.random() * this.tileCount)
        };
        
        // Reset game state
        this.gameOver = false;
        this.score = 0;
    }
    
    destroy() {
        // Clean up
        clearInterval(this.gameInterval);
        document.removeEventListener('keydown', this.handleKeyDown);
    }
}

// Initialize the game when the script loads
window.addEventListener('load', () => {
    // Check if canvas exists
    if (document.getElementById('snakeCanvas')) {
        window.snakeGame = new SnakeGameEmbed('snakeCanvas');
    }
});
