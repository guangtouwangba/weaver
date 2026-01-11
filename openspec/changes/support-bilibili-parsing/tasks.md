# Tasks: Support Bilibili Parsing

## Core Implementation
- [ ] Update `BilibiliExtractor` to support timestamped transcripts <!-- id: 400 -->
    - [ ] Modify `_get_subtitles` to extract and format timestamps (if available)
    - [ ] Implement `_format_transcript` similar to YouTube handler
- [ ] Implement Gemini audio transcription fallback <!-- id: 401 -->
    - [ ] Add `_transcribe_with_gemini` method using `yt-dlp` for Bilibili
    - [ ] Update `extract` method to use fallback flow
- [ ] Register updated extractor (if not already properly registered) <!-- id: 402 -->

## Verification
- [ ] Test with Bilibili video having subtitles <!-- id: 403 -->
- [ ] Test with Bilibili video without subtitles (Gemini fallback) <!-- id: 404 -->
