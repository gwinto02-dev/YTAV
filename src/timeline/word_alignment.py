import re
from typing import List, Dict, Any
from src.utils.text_utils import normalize_text
from src.utils.logger import logger

class WordAlignmentEngine:
    """Aligns script words to start and end timestamps using narration TTS boundary events."""

    def align_script_words(
        self,
        script_text: str,
        boundary_events: List[Dict[str, Any]],
        total_audio_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Produce a list of word-level timestamp objects for script text:
        [{"word": "Did", "clean_word": "did", "start": 0.10, "end": 0.38}, ...]
        """
        raw_words = script_text.strip().split()
        if not raw_words:
            return []

        # Filter boundary events
        sentence_events = [
            ev for ev in boundary_events
            if ev.get("type") in ("SentenceBoundary", "WordBoundary") and "offset" in ev and "duration" in ev
        ]

        if sentence_events:
            aligned_words = self._align_using_boundary_events(raw_words, sentence_events, total_audio_duration)
            if len(aligned_words) == len(raw_words):
                logger.info(f"[Alignment] Successfully aligned {len(aligned_words)} words from TTS boundary events.")
                return aligned_words

        # Proportional fallback alignment over total audio duration
        logger.info("[Alignment] Using proportional alignment engine over total audio duration.")
        return self._align_proportionally(raw_words, total_audio_duration)

    def _align_using_boundary_events(
        self,
        raw_words: List[str],
        sentence_events: List[Dict[str, Any]],
        total_audio_duration: float
    ) -> List[Dict[str, Any]]:
        """Align words using TTS sentence boundary offsets."""
        aligned_results = []
        word_index = 0

        for event in sentence_events:
            ev_start = float(event["offset"]) / 10000000.0
            ev_dur = float(event["duration"]) / 10000000.0
            ev_end = min(total_audio_duration, ev_start + ev_dur)
            ev_text = event.get("text", "")

            ev_raw_words = ev_text.strip().split()
            if not ev_raw_words:
                continue

            # Assign words in this sentence segment
            segment_words = []
            for _ in range(len(ev_raw_words)):
                if word_index < len(raw_words):
                    segment_words.append(raw_words[word_index])
                    word_index += 1

            if not segment_words:
                continue

            # Sub-divide sentence duration by word character weights
            total_chars = sum(max(1, len(normalize_text(w))) for w in segment_words)
            curr_time = ev_start

            for w in segment_words:
                clean_w = normalize_text(w)
                char_len = max(1, len(clean_w))
                w_dur = ev_dur * (char_len / float(total_chars))
                w_end = min(total_audio_duration, curr_time + w_dur)
                
                aligned_results.append({
                    "word": w,
                    "clean_word": clean_w,
                    "start": round(curr_time, 3),
                    "end": round(w_end, 3)
                })
                curr_time = w_end

        # Attach any remaining unaligned tail words
        if word_index < len(raw_words):
            tail_words = raw_words[word_index:]
            last_end = aligned_results[-1]["end"] if aligned_results else 0.0
            tail_dur = max(0.5, total_audio_duration - last_end)
            tail_chars = sum(max(1, len(normalize_text(w))) for w in tail_words)
            curr_time = last_end
            for w in tail_words:
                clean_w = normalize_text(w)
                w_dur = tail_dur * (max(1, len(clean_w)) / float(tail_chars))
                w_end = min(total_audio_duration, curr_time + w_dur)
                aligned_results.append({
                    "word": w,
                    "clean_word": clean_w,
                    "start": round(curr_time, 3),
                    "end": round(w_end, 3)
                })
                curr_time = w_end

        # Ensure monotonicity
        return self._sanitize_timestamps(aligned_results, total_audio_duration)

    def _align_proportionally(self, raw_words: List[str], total_audio_duration: float) -> List[Dict[str, Any]]:
        """Fallback proportional word alignment based on character count."""
        total_chars = sum(max(1, len(normalize_text(w))) for w in raw_words)
        aligned_results = []
        curr_time = 0.0

        for w in raw_words:
            clean_w = normalize_text(w)
            char_len = max(1, len(clean_w))
            w_dur = total_audio_duration * (char_len / float(total_chars))
            w_end = min(total_audio_duration, curr_time + w_dur)
            aligned_results.append({
                "word": w,
                "clean_word": clean_w,
                "start": round(curr_time, 3),
                "end": round(w_end, 3)
            })
            curr_time = w_end

        return self._sanitize_timestamps(aligned_results, total_audio_duration)

    def _sanitize_timestamps(self, words: List[Dict[str, Any]], total_audio_duration: float) -> List[Dict[str, Any]]:
        """Sanitize word timestamps to guarantee monotonic increasing start/end bounds."""
        if not words:
            return []

        sanitized = []
        last_end = 0.0

        for item in words:
            w = item["word"]
            clean_w = item["clean_word"]
            start = max(last_end, float(item["start"]))
            end = max(start + 0.05, float(item["end"]))
            end = min(total_audio_duration, end)

            sanitized.append({
                "word": w,
                "clean_word": clean_w,
                "start": round(start, 3),
                "end": round(end, 3)
            })
            last_end = round(end, 3)

        return sanitized
