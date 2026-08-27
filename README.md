# Amazing Facts & Mysteries Shorts Automation

A personal, production-grade Python automation system designed to dynamically create grounded, high-quality 1080x1920 vertical YouTube Shorts about science anomalies, natural phenomena, space mysteries, animals, human body facts, geography, and unsolved events.

---

## Master Timeline & Synchronization Architecture

The pipeline uses the **generated TTS narration audio as the single authoritative source of truth for all timing**:

```text
NARRATION AUDIO (edge-tts)
           ↓
TTS BOUNDARY EVENTS & WORD ALIGNMENT
           ↓
     MASTER TIMELINE
   ├── KARAOKE ASS SUBTITLES (Word-by-Word Highlighting)
   └── VISUAL SCENE TIMINGS (Derived Start / End Durations)
           ↓
FFMPEG SYNCHRONIZED VIDEO ASSEMBLY (1080x1920 Vertical MP4)
```

1. **Master Timeline (`src/timeline/`):**
   - Captures `edge-tts` `SentenceBoundary` timing events and aligns every word to accurate start and end timestamps.
   - Derives visual scene durations (`start`, `end`, `duration`) directly from narration segments.

2. **Karaoke-Style Word-by-Word Subtitles:**
   - Generates ASS (Advanced SubStation Alpha) subtitle files (`captions.ass`).
   - Displays short 3–7 word phrase groups in lower-center safe zone.
   - Highlights the currently spoken word in real-time (`&H0000FFFF` yellow/cyan) with thick outline, matching narration timing.

3. **Dynamic Topic Generation & Exhaustion Protection:**
   - Combinatorial candidate generator producing 50–100 candidate topics per batch across 7 categories.
   - 14-day cooldown protection in SQLite (`data/history.sqlite`). Zero history pollution on candidate generation.

4. **Resilient Visual Sourcing with Circuit Breaker:**
   - Visual planner extracts concise 2–6 word queries per scene.
   - Resilient provider fallback chain: `Pexels → Pixabay → Wikimedia Commons → Local Fallback Backdrops`.
   - Circuit breaker health state disables failing network providers after 2 errors for the current run.

5. **FFmpeg Video Assembly & Synchronization QA:**
   - Exports 1080x1920 30fps vertical MP4 shorts.
   - Deterministic QA at every stage, including `SynchronizationQA` verifying monotonic word timestamps, scene continuity, and video/audio duration match (`diff < 0.5s`).

---

## Configuration

Subtitles and karaoke styling are fully configurable in `config/settings.py` (or `.env`):
- `CAPTION_FONT_SIZE` (default: `24`)
- `CAPTION_FONT_FAMILY` (default: `"Arial"`)
- `CAPTION_PRIMARY_COLOR` (default: `"&H00FFFFFF"` white)
- `CAPTION_HIGHLIGHT_COLOR` (default: `"&H0000FFFF"` vibrant yellow)
- `CAPTION_OUTLINE_THICKNESS` (default: `3`)
- `CAPTION_WORDS_PER_GROUP` (default: `5`)
- `CAPTION_VERTICAL_POSITION` (default: `220`)

---

## Execution Commands

### Run Synchronized Production Pipeline
```bash
python main.py
```

### Run Full Test Suite
```bash
pytest -q
```

---

## Output Structure

- `output/videos/`: Final vertical MP4 video files (`short_YYYYMMDD_HHMMSS.mp4`)
- `output/reports/`: Markdown execution summaries (`report_YYYYMMDD_HHMMSS_topic.md`)
- `output/metadata/`: JSON metadata containing word alignment, scene timing, and health state (`metadata_YYYYMMDD_HHMMSS_topic.json`)
- `data/history.sqlite`: Persistent SQLite database storing topic usage and run history
