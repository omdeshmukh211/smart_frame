/**
 * Qt WebEngine Bridge
 * ====================
 * Provides integration between the web UI and PyQt5 wrapper.
 * Allows launching external Chromium for YouTube Music.
 * 
 * This file is automatically loaded by the Smart Frame UI.
 * When running in QtWebEngine, it provides access to native functions.
 * When running in a regular browser, it provides fallback behavior.
 */

(function() {
    'use strict';
    
    // Global Qt bridge object
    window.QtBridge = {
        _initialized: false,
        _channel: null,
        _chromiumBridge: null,
        _callbacks: [],
        
        /**
         * Check if running inside Qt WebEngine
         */
        isQtWebEngine: function() {
            return typeof qt !== 'undefined' && qt.webChannelTransport;
        },
        
        /**
         * Initialize the Qt WebChannel connection
         * Call this once when the app starts
         */
        init: function(callback) {
            var self = this;
            
            if (!this.isQtWebEngine()) {
                console.log('QtBridge: Not running in Qt WebEngine, using fallback mode');
                this._initialized = true;
                if (callback) callback(false);
                return;
            }
            
            // Load QWebChannel library if not already loaded
            if (typeof QWebChannel === 'undefined') {
                var script = document.createElement('script');
                script.src = 'qrc:///qtwebchannel/qwebchannel.js';
                script.onload = function() {
                    self._initChannel(callback);
                };
                script.onerror = function() {
                    console.error('QtBridge: Failed to load QWebChannel');
                    self._initialized = true;
                    if (callback) callback(false);
                };
                document.head.appendChild(script);
            } else {
                this._initChannel(callback);
            }
        },
        
        /**
         * Internal: Initialize WebChannel
         */
        _initChannel: function(callback) {
            var self = this;
            
            try {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    self._channel = channel;
                    self._chromiumBridge = channel.objects.chromiumBridge;
                    self._initialized = true;
                    console.log('QtBridge: WebChannel initialized successfully');
                    
                    // Process any pending callbacks
                    self._callbacks.forEach(function(cb) {
                        cb(self._chromiumBridge);
                    });
                    self._callbacks = [];
                    
                    if (callback) callback(true);
                });
            } catch (e) {
                console.error('QtBridge: Failed to initialize WebChannel:', e);
                this._initialized = true;
                if (callback) callback(false);
            }
        },
        
        /**
         * Execute function when bridge is ready
         */
        whenReady: function(callback) {
            if (this._initialized && this._chromiumBridge) {
                callback(this._chromiumBridge);
            } else if (this._initialized) {
                // Initialized but no bridge (fallback mode)
                callback(null);
            } else {
                // Not yet initialized, queue callback
                this._callbacks.push(callback);
            }
        },
        
        /**
         * Launch YouTube Music in external Chromium browser
         * @param {string} artist - Optional artist/song to search for
         * @param {function} callback - Optional callback(success)
         */
        launchYouTubeMusic: function(artist, callback) {
            var self = this;
            artist = artist || '';
            
            if (this.isQtWebEngine()) {
                this.whenReady(function(bridge) {
                    if (bridge) {
                        try {
                            bridge.launch_youtube_music(artist);
                            console.log('QtBridge: Launched YouTube Music with:', artist);
                            if (callback) callback(true);
                        } catch (e) {
                            console.error('QtBridge: Failed to launch YouTube Music:', e);
                            if (callback) callback(false);
                        }
                    } else {
                        console.warn('QtBridge: Bridge not available');
                        if (callback) callback(false);
                    }
                });
            } else {
                // Fallback: Use Flask API
                console.log('QtBridge: Using Flask API fallback for YouTube Music');
                fetch('/api/music/play', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ artist: artist })
                })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (callback) callback(data.success);
                })
                .catch(function(e) {
                    console.error('QtBridge: Flask API error:', e);
                    if (callback) callback(false);
                });
            }
        },
        
        /**
         * Stop YouTube Music (close Chromium)
         * @param {function} callback - Optional callback(success)
         */
        stopYouTubeMusic: function(callback) {
            var self = this;
            
            if (this.isQtWebEngine()) {
                this.whenReady(function(bridge) {
                    if (bridge) {
                        try {
                            bridge.stop_youtube_music();
                            console.log('QtBridge: Stopped YouTube Music');
                            if (callback) callback(true);
                        } catch (e) {
                            console.error('QtBridge: Failed to stop YouTube Music:', e);
                            if (callback) callback(false);
                        }
                    } else {
                        if (callback) callback(false);
                    }
                });
            } else {
                // Fallback: Use Flask API
                fetch('/api/music/stop', { method: 'POST' })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (callback) callback(data.success);
                })
                .catch(function(e) {
                    console.error('QtBridge: Flask API error:', e);
                    if (callback) callback(false);
                });
            }
        }
    };
    
    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            window.QtBridge.init();
        });
    } else {
        window.QtBridge.init();
    }
    
    console.log('QtBridge: Module loaded');
})();
