from typing import List, Dict, Any
from config.settings import CAPTION_WORDS_PER_GROUP
from src.timeline.word_alignment import WordAlignmentEngine
from src.timeline.scene_timing import SceneTimingCalculator
from src.utils.logger import logger

class TimelineBuilder:
    """Builds unified Master Timeline containing word timestamps, karaoke caption groups, and scene timings."""

    def __init__(self):
        self.word_aligner = WordAlignmentEngine()
        self.scene_calculator = SceneTimingCalculator()

    def build_master_timeline(
        self,
        script_text: str,
        topic_name: str,
        total_audio_duration: float,
        boundary_events: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build master timeline driven by generated narration audio timing.
        """
        logger.info("[Timeline] Constructing Master Timeline from narration audio...")
        if boundary_events is None:
            boundary_events = []

        # 1. Align word timestamps
        words = self.word_aligner.align_script_words(
            script_text=script_text,
            boundary_events=boundary_events,
            total_audio_duration=total_audio_duration
        )

        # 2. Build phrase caption groups (3-7 words per group)
        caption_groups = self._build_caption_groups(words, target_group_size=CAPTION_WORDS_PER_GROUP)

        # 3. Calculate visual scene timings synchronized to timeline
        scenes = self.scene_calculator.calculate_scene_timings(
            script_text=script_text,
            words=words,
            topic_name=topic_name,
            total_audio_duration=total_audio_duration
        )

        logger.info(
            f"[Timeline] Master Timeline built: Duration={total_audio_duration:.2f}s, "
            f"Words={len(words)}, CaptionGroups={len(caption_groups)}, Scenes={len(scenes)}"
        )

        return {
            "total_duration": total_audio_duration,
            "words": words,
            "caption_groups": caption_groups,
            "narration_segments": scenes,
            "scenes": scenes
        }

    def _build_caption_groups(
        self,
        words: List[Dict[str, Any]],
        target_group_size: int = 5
    ) -> List[Dict[str, Any]]:
        """Group aligned words into short phrase groups for karaoke captioning."""
        if not words:
            return []

        groups = []
        chunk_size = max(3, min(7, target_group_size))

        for i in range(0, len(words), chunk_size):
            group_words = words[i:i + chunk_size]
            g_start = group_words[0]["start"]
            g_end = group_words[-1]["end"]
            phrase = " ".join([w["word"] for w in group_words])

            groups.append({
                "group_index": len(groups) + 1,
                "start": g_start,
                "end": g_end,
                "duration": round(g_end - g_start, 3),
                "phrase": phrase,
                "words": group_words
            })

        return groups
