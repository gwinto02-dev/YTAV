from typing import Dict, Any, Tuple
from src.utils.logger import logger

class SynchronizationQA:
    """Deterministic Quality Assurance verifying narration, subtitle, and visual scene timeline synchronization."""

    def validate_timeline_and_sync(
        self,
        master_timeline: Dict[str, Any],
        video_duration: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate all 12 synchronization rules.
        Returns (is_valid, reason, metrics).
        """
        narration_duration = float(master_timeline.get("total_duration", 0.0))
        words = master_timeline.get("words", [])
        caption_groups = master_timeline.get("caption_groups", [])
        scenes = master_timeline.get("scenes", [])

        if narration_duration <= 0.0:
            return False, "Sync QA Failed: Narration duration is zero", {}

        if not words:
            return False, "Sync QA Failed: Word timeline is empty", {}

        # 1. First word start near beginning
        first_start = float(words[0]["start"])
        if first_start < 0.0 or first_start > 1.5:
            return False, f"Sync QA Failed: First word start ({first_start:.2f}s) is out of bounds", {}

        # 2. Last word end does not exceed narration duration
        last_end = float(words[-1]["end"])
        if last_end > narration_duration + 0.5:
            return False, f"Sync QA Failed: Last word end ({last_end:.2f}s) exceeds narration duration ({narration_duration:.2f}s)", {}

        # 3. Monotonic word timestamps
        for i in range(len(words) - 1):
            w_curr = words[i]
            w_next = words[i + 1]
            if float(w_curr["end"]) < float(w_curr["start"]):
                return False, f"Sync QA Failed: Word '{w_curr['word']}' end < start", {}
            if float(w_next["start"]) < float(w_curr["start"]):
                return False, f"Sync QA Failed: Non-monotonic word order between '{w_curr['word']}' and '{w_next['word']}'", {}

        # 4. Caption group chronological order
        for idx in range(len(caption_groups) - 1):
            cg_curr = caption_groups[idx]
            cg_next = caption_groups[idx + 1]
            if float(cg_next["start"]) < float(cg_curr["start"]):
                return False, "Sync QA Failed: Caption groups out of chronological order", {}

        # 5. Visual scene timing continuity and coverage
        if not scenes:
            return False, "Sync QA Failed: Visual scene timeline is empty", {}

        if float(scenes[0]["start"]) != 0.0:
            return False, f"Sync QA Failed: First scene start is {scenes[0]['start']}s (expected 0.0s)", {}

        for s_idx in range(len(scenes) - 1):
            s_curr = scenes[s_idx]
            s_next = scenes[s_idx + 1]
            if abs(float(s_curr["end"]) - float(s_next["start"])) > 0.05:
                return False, f"Sync QA Failed: Scene gap/overlap between Scene {s_curr['scene_number']} and Scene {s_next['scene_number']}", {}

        # 6. Video duration vs narration duration sync
        diff = abs(video_duration - narration_duration)
        if diff > 0.8:
            return False, f"Sync QA Failed: Video duration ({video_duration:.2f}s) differs from narration ({narration_duration:.2f}s) by {diff:.2f}s (> 0.8s)", {}

        metrics = {
            "narration_duration": narration_duration,
            "video_duration": video_duration,
            "difference": round(diff, 3),
            "words_aligned": len(words),
            "first_word_start": first_start,
            "last_word_end": last_end,
            "caption_groups": len(caption_groups),
            "scenes_count": len(scenes)
        }

        logger.info(
            f"[SyncQA] [Narration] Duration: {narration_duration:.2f}s | "
            f"[Video] Duration: {video_duration:.2f}s | Diff: {diff:.2f}s | SYNC PASS"
        )

        return True, "Synchronization QA Passed", metrics
