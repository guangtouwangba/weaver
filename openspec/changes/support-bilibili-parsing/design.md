# Design: Bilibili Parsing Support

## Context
The current `BilibiliExtractor` is limited compared to `YouTubeExtractor`. It lacks:
1.  Timestamped transcripts (crucial for "Mindmap Video Navigation").
2.  Audio transcription fallback (for videos without subtitles).

## Proposed Changes

### 1. Enhanced Transcript Formatting
- Modify `BilibiliExtractor._get_subtitles` to return structured data (start, duration, text) instead of just plain text.
- Implement `_format_transcript` (similar to `YouTubeExtractor`) to inject `[TIME:MM:SS]` markers.
- This aligns Bilibili output with the format required by the frontend video player integration.

### 2. Audio Transcription Fallback
- Reuse `research_agent.infrastructure.llm.gemini_audio`.
- Function `transcribe_youtube_video` currently implies YouTube-specifics.
- **Refactoring**: Rename `transcribe_youtube_video` to `transcribe_video` (or similar generic name) and ensure `yt-dlp` usage is platform-agnostic or supports Bilibili explicitly.
- `yt-dlp` naturally supports Bilibili, so the core download logic should remain largely the same, but we need to verify cookie handling or User-Agent if Bilibili blocks automated requests.
    - *Note*: Bilibili often requires specific headers/cookies. The `bilibili-api-python` library handles some of this, but `yt-dlp` might need help.
    - For now, we will attempt standard `yt-dlp` usage.

### 3. Architecture
- `BilibiliExtractor` will follow the same try-catch fallback pattern as `YouTubeExtractor`:
    1.  Get Metadata.
    2.  Try `bilibili-api` for subtitles (fast, low cost).
    3.  If fail, try `Gemini` audio transcription (slower, higher cost).

## Alternatives Considered
- **Client-side parsing**: Rejected. We want a unified backend API for all URL types.
- **Separate Bilibili-only transcriber**: Rejected. `Gemini` is our standard multimodal model.

## Risks
- **Rate Limiting / Captcha**: Bilibili is aggressive with anti-bot. `bilibili-api-python` helps, but `yt-dlp` might get blocked.
    - *Mitigation*: We will proceed with `yt-dlp` as best-effort fallback. If it fails, we return available metadata.
