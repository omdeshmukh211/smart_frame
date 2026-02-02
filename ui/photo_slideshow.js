/**
 * Photo Slideshow Controller
 * Manages the photo slideshow functionality for the smart frame.
 * 
 * Features:
 * - Auto-advances every 10 minutes
 * - Click/tap to advance manually
 * - Smooth fade transitions
 * - Continuous loop through all photos
 * - Handles errors gracefully
 */

class PhotoSlideshowController {
    constructor() {
        // Configuration
        this.AUTO_ADVANCE_INTERVAL = 10 * 60 * 1000; // 10 minutes in milliseconds
        this.FADE_DURATION = 1000; // 1 second fade
        
        // State
        this.autoAdvanceTimer = null;
        this.currentPhoto = null;
        this.isTransitioning = false;
        
        // DOM elements
        this.photoFrame = null;
        this.photoContainer = null;
        this.currentImage = null;
        this.nextImage = null;
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the slideshow controller
     */
    init() {
        console.log('Initializing photo slideshow...');
        
        // Get or create DOM elements
        this.setupDOM();
        
        // Load the first photo
        this.loadInitialPhoto();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Photo slideshow initialized');
    }
    
    /**
     * Set up DOM elements for the slideshow
     */
    setupDOM() {
        // Get the photo frame container
        this.photoFrame = document.getElementById('photo-frame');
        
        if (!this.photoFrame) {
            console.error('Photo frame element not found!');
            return;
        }
        
        // Clear existing content
        this.photoFrame.innerHTML = '';
        
        // Create photo container with two image layers for crossfade
        this.photoContainer = document.createElement('div');
        this.photoContainer.className = 'photo-container';
        
        // Create first image element (initially visible)
        this.currentImage = document.createElement('img');
        this.currentImage.className = 'photo-image current';
        this.currentImage.alt = 'Photo slideshow';
        
        // Create second image element (for transitions)
        this.nextImage = document.createElement('img');
        this.nextImage.className = 'photo-image next';
        this.nextImage.alt = 'Photo slideshow';
        
        // Add images to container
        this.photoContainer.appendChild(this.currentImage);
        this.photoContainer.appendChild(this.nextImage);
        
        // Add container to photo frame
        this.photoFrame.appendChild(this.photoContainer);
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Click/tap to advance to next photo
        if (this.photoFrame) {
            this.photoFrame.addEventListener('click', () => {
                console.log('Photo frame clicked - advancing to next photo');
                this.advanceToNext();
            });
        }
    }
    
    /**
     * Load the initial photo on page load
     */
    async loadInitialPhoto() {
        try {
            const response = await fetch('/api/photos/current');
            const data = await response.json();
            
            if (data.success && data.photo) {
                console.log(`Loading initial photo: ${data.photo} (${data.index + 1}/${data.total})`);
                this.currentPhoto = data.photo;
                
                // Set the image source
                this.currentImage.src = `/photos/${encodeURIComponent(data.photo)}`;
                
                // Start auto-advance timer
                this.startAutoAdvanceTimer();
            } else {
                console.warn('No photos available');
                this.showPlaceholder();
            }
        } catch (error) {
            console.error('Error loading initial photo:', error);
            this.showPlaceholder();
        }
    }
    
    /**
     * Advance to the next photo
     */
    async advanceToNext() {
        // Prevent multiple transitions at once
        if (this.isTransitioning) {
            console.log('Transition already in progress, skipping...');
            return;
        }
        
        try {
            this.isTransitioning = true;
            
            // Call API to get next photo
            const response = await fetch('/api/photos/next', {
                method: 'POST',
            });
            const data = await response.json();
            
            if (data.success && data.photo) {
                console.log(`Advancing to photo: ${data.photo} (${data.index + 1}/${data.total})`);
                
                // Load new photo into the hidden next image
                await this.loadImage(this.nextImage, `/photos/${encodeURIComponent(data.photo)}`);
                
                // Perform crossfade transition
                await this.crossfade();
                
                // Update current photo reference
                this.currentPhoto = data.photo;
                
                // Reset auto-advance timer
                this.resetAutoAdvanceTimer();
            } else {
                console.warn('Failed to get next photo:', data.error);
            }
        } catch (error) {
            console.error('Error advancing to next photo:', error);
        } finally {
            this.isTransitioning = false;
        }
    }
    
    /**
     * Load an image and wait for it to complete
     * @param {HTMLImageElement} imgElement - Image element to load into
     * @param {string} src - Image source URL
     * @returns {Promise} Promise that resolves when image is loaded
     */
    loadImage(imgElement, src) {
        return new Promise((resolve, reject) => {
            imgElement.onload = () => resolve();
            imgElement.onerror = () => reject(new Error(`Failed to load image: ${src}`));
            imgElement.src = src;
        });
    }
    
    /**
     * Perform a crossfade transition between current and next image
     * @returns {Promise} Promise that resolves when transition is complete
     */
    crossfade() {
        return new Promise((resolve) => {
            // Show the next image
            this.nextImage.classList.add('visible');
            
            // Wait for transition to complete
            setTimeout(() => {
                // Swap the images: current becomes next, next becomes current
                [this.currentImage, this.nextImage] = [this.nextImage, this.currentImage];
                
                // Update classes
                this.currentImage.classList.remove('next', 'visible');
                this.currentImage.classList.add('current');
                this.nextImage.classList.remove('current');
                this.nextImage.classList.add('next');
                
                resolve();
            }, this.FADE_DURATION);
        });
    }
    
    /**
     * Start the auto-advance timer
     */
    startAutoAdvanceTimer() {
        console.log(`Starting auto-advance timer (${this.AUTO_ADVANCE_INTERVAL / 1000}s)`);
        this.autoAdvanceTimer = setInterval(() => {
            console.log('Auto-advance timer triggered');
            this.advanceToNext();
        }, this.AUTO_ADVANCE_INTERVAL);
    }
    
    /**
     * Stop the auto-advance timer
     */
    stopAutoAdvanceTimer() {
        if (this.autoAdvanceTimer) {
            console.log('Stopping auto-advance timer');
            clearInterval(this.autoAdvanceTimer);
            this.autoAdvanceTimer = null;
        }
    }
    
    /**
     * Reset the auto-advance timer (restart from 0)
     */
    resetAutoAdvanceTimer() {
        this.stopAutoAdvanceTimer();
        this.startAutoAdvanceTimer();
    }
    
    /**
     * Show placeholder when no photos are available
     */
    showPlaceholder() {
        if (this.photoFrame) {
            this.photoFrame.innerHTML = `
                <div class="photo-frame-content">
                    <span class="photo-frame-text">Photo Frame</span>
                    <span class="photo-frame-subtext">No photos available</span>
                </div>
            `;
        }
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        this.stopAutoAdvanceTimer();
        
        if (this.photoFrame) {
            this.photoFrame.removeEventListener('click', this.advanceToNext);
        }
    }
}

// Global instance
let photoSlideshow = null;

/**
 * Initialize the photo slideshow
 * Call this when the page loads or when the clock screen is shown
 */
function initPhotoSlideshow() {
    if (!photoSlideshow) {
        photoSlideshow = new PhotoSlideshowController();
    }
}

/**
 * Destroy the photo slideshow
 * Call this to clean up resources
 */
function destroyPhotoSlideshow() {
    if (photoSlideshow) {
        photoSlideshow.destroy();
        photoSlideshow = null;
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPhotoSlideshow);
} else {
    // DOM is already ready
    initPhotoSlideshow();
}
