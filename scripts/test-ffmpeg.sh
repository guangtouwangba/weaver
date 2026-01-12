#!/bin/bash
# Test script to verify ffmpeg and ffprobe are available

echo "Testing ffmpeg installation..."
echo ""

echo "1. Checking ffmpeg:"
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg found at: $(which ffmpeg)"
    ffmpeg -version | head -n 1
else
    echo "✗ ffmpeg not found"
    exit 1
fi

echo ""
echo "2. Checking ffprobe:"
if command -v ffprobe &> /dev/null; then
    echo "✓ ffprobe found at: $(which ffprobe)"
    ffprobe -version | head -n 1
else
    echo "✗ ffprobe not found"
    exit 1
fi

echo ""
echo "3. Testing yt-dlp with ffmpeg:"
python3 -c "
import yt_dlp
import sys

# Test if yt-dlp can find ffmpeg
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'ffmpeg_location': '/usr/bin',
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Try to get postprocessor
        pp = ydl.get_postprocessor('FFmpegExtractAudio')
        if pp:
            print('✓ yt-dlp can access FFmpeg postprocessor')
        else:
            print('✗ yt-dlp cannot find FFmpeg postprocessor')
            sys.exit(1)
except Exception as e:
    print(f'✗ Error testing yt-dlp: {e}')
    sys.exit(1)
"

echo ""
echo "All checks passed! ✓"
