# Proposal: Support Bilibili Parsing

## Goal
Enable full support for Bilibili video parsing, matching the capabilities of the existing YouTube parser. This ensures consistency for the "Mindmap Video Navigation" feature across platforms.

## Capabilities
- **Timestamped Transcripts**: Format Bilibili subtitles with `[TIME:MM:SS]` markers to enable mindmap node-to-video navigation.
- **Audio Transcription Fallback**: Automatically fall back to Gemini-powered audio transcription when Bilibili subtitles are unavailable.

## Background
The current `BilibiliExtractor` (in `handlers/bilibili.py`) is basic:
- It extracts metadata and plain text subtitles.
- **Problem**: It discards timestamp information, breaking the mindmap navigation feature which relies on `[TIME:MM:SS]` markers.
- **Problem**: It fails specific videos that don't have user-submitted subtitles, whereas `youtube.py` falls back to AI audio transcription.

## Plan
1.  **Refactor `GeminiAudioTranscriber`**:
    - Current implementation hardcodes `youtube.com` URL generation.
    - Change it to accept a full URL, making it platform-agnostic (leveraging `yt-dlp`'s broad support).
2.  **Update `BilibiliExtractor`**:
    - Modify `_get_subtitles` to preserve timestamps from `bilibili-api`.
    - Implement `_format_transcript` (shared logic with YouTube logic can be consolidated if possible, or duplicated for independence) to insert markers.
    - Integrate the refactored `GeminiAudioTranscriber` as a fallback.
