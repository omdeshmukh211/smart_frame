# Photo Slideshow - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RASPBERRY PI 4                                   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FLASK APPLICATION (app.py)                     │   │
│  │                                                                   │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │            Photo API Endpoints                             │ │   │
│  │  │                                                            │ │   │
│  │  │  GET  /api/photos/current    → Get current photo info    │ │   │
│  │  │  POST /api/photos/next       → Advance to next photo     │ │   │
│  │  │  POST /api/photos/previous   → Go to previous photo      │ │   │
│  │  │  GET  /photos/<filename>     → Serve photo file          │ │   │
│  │  │  POST /api/photos/rescan     → Rescan photos directory   │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  │                              ↕                                    │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │       PhotoManager (backend/photo_manager.py)             │ │   │
│  │  │                                                            │ │   │
│  │  │  • Scans photos directory on startup                      │ │   │
│  │  │  • Maintains sorted list of all photos                    │ │   │
│  │  │  • Tracks current photo index                             │ │   │
│  │  │  • Provides next/previous navigation                      │ │   │
│  │  │  • Loops back to start after last photo                   │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  │                              ↕                                    │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │      Photos Directory                                      │ │   │
│  │  │      /home/raspberrypi4/projects/smart_frame/photos/       │ │   │
│  │  │                                                            │ │   │
│  │  │      photo1.jpg                                            │ │   │
│  │  │      photo2.png                                            │ │   │
│  │  │      vacation/                                             │ │   │
│  │  │        ├── beach.jpg                                       │ │   │
│  │  │        └── sunset.jpg                                      │ │   │
│  │  │      family/                                               │ │   │
│  │  │        └── birthday.jpg                                    │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↕ HTTP
┌─────────────────────────────────────────────────────────────────────────┐
│                    BROWSER (Chromium/QtWebEngine)                        │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    HTML (ui/index.html)                           │  │
│  │                                                                   │  │
│  │  <div id="photo-frame" class="photo-frame">                      │  │
│  │    <!-- Photo slideshow displays here -->                        │  │
│  │  </div>                                                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              ↕                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │          JavaScript (ui/photo_slideshow.js)                       │  │
│  │          PhotoSlideshowController                                 │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │ INITIALIZATION                                          │    │  │
│  │  │ 1. Create photo container with 2 image elements         │    │  │
│  │  │ 2. Fetch current photo from API                         │    │  │
│  │  │ 3. Load first photo into currentImage element           │    │  │
│  │  │ 4. Start 10-minute auto-advance timer                   │    │  │
│  │  │ 5. Add click event listener                             │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │ AUTO-ADVANCE LOOP (every 10 minutes)                    │    │  │
│  │  │                                                          │    │  │
│  │  │ Timer triggers:                                          │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ 1. POST /api/photos/next                                │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ 2. Receive next photo info                              │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ 3. Load image into nextImage element (hidden)           │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ 4. Perform crossfade transition (1 second)              │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ 5. Swap currentImage ↔ nextImage                        │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ 6. Reset timer and repeat                               │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │ MANUAL ADVANCE (on tap/click)                           │    │  │
│  │  │                                                          │    │  │
│  │  │ User taps photo:                                         │    │  │
│  │  │   ↓                                                      │    │  │
│  │  │ Same as auto-advance, but also:                          │    │  │
│  │  │ • Cancels current timer                                  │    │  │
│  │  │ • Advances to next photo                                 │    │  │
│  │  │ • Starts new 10-minute timer                             │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              ↕                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    CSS (ui/style.css)                             │  │
│  │                                                                   │  │
│  │  .photo-container {                                              │  │
│  │    /* Container for crossfade effect */                          │  │
│  │  }                                                               │  │
│  │                                                                   │  │
│  │  .photo-image {                                                  │  │
│  │    transition: opacity 1s ease-in-out; /* Smooth fade */        │  │
│  │    object-fit: contain; /* Maintain aspect ratio */             │  │
│  │  }                                                               │  │
│  │                                                                   │  │
│  │  .photo-image.current {                                          │  │
│  │    opacity: 1; /* Visible */                                     │  │
│  │  }                                                               │  │
│  │                                                                   │  │
│  │  .photo-image.next {                                             │  │
│  │    opacity: 0; /* Hidden */                                      │  │
│  │  }                                                               │  │
│  │                                                                   │  │
│  │  .photo-image.next.visible {                                     │  │
│  │    opacity: 1; /* Fade in */                                     │  │
│  │  }                                                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Crossfade Transition Sequence

```
BEFORE TRANSITION:
┌──────────────────┐
│  currentImage    │  opacity: 1  (visible)
│  (photo1.jpg)    │  z-index: 1
└──────────────────┘
┌──────────────────┐
│  nextImage       │  opacity: 0  (hidden)
│  (empty)         │  z-index: 2
└──────────────────┘

STEP 1 - Load next photo:
┌──────────────────┐
│  currentImage    │  opacity: 1  (visible)
│  (photo1.jpg)    │  z-index: 1
└──────────────────┘
┌──────────────────┐
│  nextImage       │  opacity: 0  (hidden, but loaded)
│  (photo2.jpg)    │  z-index: 2
└──────────────────┘

STEP 2 - Fade in next photo (1 second):
┌──────────────────┐
│  currentImage    │  opacity: 1 → 1  (still visible)
│  (photo1.jpg)    │  z-index: 1
└──────────────────┘
┌──────────────────┐
│  nextImage       │  opacity: 0 → 1  (fading in)
│  (photo2.jpg)    │  z-index: 2  ← on top, so it covers currentImage
└──────────────────┘

STEP 3 - Swap roles after transition:
┌──────────────────┐
│  currentImage    │  opacity: 1  (now showing photo2.jpg)
│  (photo2.jpg)    │  z-index: 1  ← swapped
└──────────────────┘
┌──────────────────┐
│  nextImage       │  opacity: 0  (now empty, ready for next photo)
│  (photo1.jpg)    │  z-index: 2  ← swapped
└──────────────────┘

Ready for next transition! ↻
```

## Data Flow Diagram

```
┌───────────────┐
│   Page Load   │
└───────┬───────┘
        ↓
┌───────────────────────────────────┐
│ PhotoSlideshowController.init()  │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ GET /api/photos/current           │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ PhotoManager.get_current_photo()  │
│ Returns: "photo1.jpg"             │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ Load image:                       │
│ <img src="/photos/photo1.jpg">    │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ Start 10-minute timer             │
└───────┬───────────────────────────┘
        ↓
        ⏱ Wait 10 minutes or tap...
        ↓
┌───────────────────────────────────┐
│ POST /api/photos/next             │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ PhotoManager.get_next_photo()     │
│ • Increment index: 0 → 1          │
│ • Loop if needed: 449 → 0         │
│ Returns: "photo2.jpg"             │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ Preload next image (hidden)       │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ Crossfade transition (1s)         │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ Swap image elements               │
└───────┬───────────────────────────┘
        ↓
┌───────────────────────────────────┐
│ Reset timer                       │
└───────┬───────────────────────────┘
        ↓
        ↺ Loop back to timer wait
```

## Performance Optimizations

```
┌─────────────────────────────────────────────────────────────┐
│                   PERFORMANCE FEATURES                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. MEMORY EFFICIENCY                                        │
│     • Only 2 images in memory at any time                    │
│     • No preloading of entire collection                     │
│     • Previous images garbage collected                      │
│                                                              │
│  2. RENDERING OPTIMIZATION (Raspberry Pi 4)                  │
│     • Hardware acceleration: will-change: opacity            │
│     • GPU compositing: transform: translateZ(0)              │
│     • Backface culling: backface-visibility: hidden          │
│     • Smooth antialiasing: -webkit-optimize-contrast         │
│                                                              │
│  3. NETWORK EFFICIENCY                                       │
│     • Photos served directly by Flask (no copying)           │
│     • Browser caching of image files                         │
│     • On-demand loading (not bulk preload)                   │
│                                                              │
│  4. TRANSITION PERFORMANCE                                   │
│     • CSS transitions (GPU accelerated)                      │
│     • Opacity-only animation (fast)                          │
│     • No JavaScript animation loops                          │
│                                                              │
│  5. FILESYSTEM EFFICIENCY                                    │
│     • Single directory scan on startup                       │
│     • In-memory photo list                                   │
│     • Index-based navigation (O(1) lookup)                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Interactions

```
  app.py                photo_manager.py           photos/
     │                         │                      │
     │ imports                 │                      │
     ├────────────────────────→│                      │
     │                         │                      │
     │ get_photo_manager()     │                      │
     ├────────────────────────→│                      │
     │                         │ scan_photos()        │
     │                         ├─────────────────────→│
     │                         │←─────────────────────┤
     │                         │ Returns photo list   │
     │                         │                      │
     │ API request:            │                      │
     │ /api/photos/next        │                      │
     ├────────────────────────→│                      │
     │                         │ get_next_photo()     │
     │                         │ • index++            │
     │                         │ • loop if needed     │
     │←────────────────────────┤                      │
     │ Returns: "photo.jpg"    │                      │
     │                         │                      │
     │ API request:            │                      │
     │ /photos/photo.jpg       │                      │
     ├────────────────────────→│ get_photo_path()     │
     │                         ├─────────────────────→│
     │                         │←─────────────────────┤
     │                         │ File path            │
     │                         │                      │
     │ send_from_directory()   │                      │
     ├─────────────────────────┼─────────────────────→│
     │←────────────────────────┼──────────────────────┤
     │ Photo file bytes        │                      │
```

---

**Visual Guide Complete!**

This diagram shows how all the components work together to create
a smooth, efficient photo slideshow experience on your Raspberry Pi 4.
