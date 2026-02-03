#!/bin/bash
# Test script for YouTube Music Player
# Run this on your Raspberry Pi to verify the installation

echo "=========================================="
echo "YouTube Music Player - Installation Test"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

echo "1. Checking Python version..."
python3 --version &> /dev/null
test_result $? "Python 3 is installed"

echo ""
echo "2. Checking yt-dlp installation..."
yt-dlp --version &> /dev/null
test_result $? "yt-dlp is installed"

echo ""
echo "3. Checking mpv installation..."
mpv --version &> /dev/null
test_result $? "mpv is installed"

echo ""
echo "4. Checking ffmpeg installation..."
ffmpeg -version &> /dev/null
test_result $? "ffmpeg is installed"

echo ""
echo "5. Testing yt-dlp YouTube search..."
SEARCH_RESULT=$(yt-dlp --default-search "ytsearch1" --skip-download --print "%(id)s" "test" 2>/dev/null)
if [ -n "$SEARCH_RESULT" ]; then
    test_result 0 "YouTube search works"
else
    test_result 1 "YouTube search failed (check internet connection)"
fi

echo ""
echo "6. Checking music_player.py exists..."
if [ -f "backend/music_player.py" ]; then
    test_result 0 "music_player.py found"
else
    test_result 1 "music_player.py not found"
fi

echo ""
echo "7. Checking music player UI files..."
if [ -f "ui/music_player.js" ] && [ -f "ui/music_player.css" ]; then
    test_result 0 "UI files found"
else
    test_result 1 "UI files missing"
fi

echo ""
echo "8. Testing Python import..."
python3 -c "from backend.music_player import get_music_player" 2>/dev/null
test_result $? "Python import successful"

echo ""
echo "9. Checking audio device..."
aplay -l &> /dev/null
test_result $? "Audio device detected"

echo ""
echo "10. Checking Flask app file..."
if [ -f "app.py" ]; then
    grep -q "music_player" app.py
    test_result $? "app.py has music_player integration"
else
    test_result 1 "app.py not found"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start the Flask app: python3 app.py"
    echo "2. Open browser: http://localhost:5000"
    echo "3. Click Music button and test playback"
    echo ""
    echo "For API testing, run:"
    echo "  curl -X POST http://localhost:5000/api/music/search \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"query\": \"lofi music\"}'"
else
    echo -e "${YELLOW}Some tests failed. See docs/MUSIC_PLAYER_SETUP.md for troubleshooting.${NC}"
    echo ""
    echo "Quick fixes:"
    [ -z "$(command -v yt-dlp)" ] && echo "  - Install yt-dlp: pip install yt-dlp"
    [ -z "$(command -v mpv)" ] && echo "  - Install mpv: sudo apt-get install mpv"
    [ -z "$(command -v ffmpeg)" ] && echo "  - Install ffmpeg: sudo apt-get install ffmpeg"
fi

echo ""
