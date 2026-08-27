import re
from typing import List, Dict, Any
from src.utils.text_utils import extract_concise_keywords
from src.utils.logger import logger

class SceneTimingCalculator:
    """Calculates visual scene start, end, and duration timestamps from word alignment timeline."""

    def calculate_scene_timings(
        self,
        script_text: str,
        words: List[Dict[str, Any]],
        topic_name: str,
        total_audio_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Derive scene start/end timestamps directly from word-level timeline.
        """
        if not words:
            return []

        # Split script text into sentences for semantic segmentation
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script_text) if len(s.strip()) > 10]
        if not sentences:
            sentences = [script_text]

        total_scenes = max(5, min(8, len(sentences)))
        words_per_scene = max(1, len(words) // total_scenes)

        scenes = []
        used_queries = set()
        topic_keywords = extract_concise_keywords(topic_name, max_words=3)

        for i in range(total_scenes):
            w_start_idx = i * words_per_scene
            if i == total_scenes - 1:
                scene_words = words[w_start_idx:]
            else:
                scene_words = words[w_start_idx:w_start_idx + words_per_scene]

            if not scene_words:
                continue

            scene_start = scene_words[0]["start"]
            scene_end = scene_words[-1]["end"]
            
            # Continuous boundary adjustments (scene_start connects to previous scene_end)
            if i == 0:
                scene_start = 0.0
            else:
                scene_start = scenes[-1]["end"]

            if i == total_scenes - 1:
                scene_end = total_audio_duration

            duration = max(0.5, round(scene_end - scene_start, 3))
            narration_chunk = " ".join([w["word"] for w in scene_words])

            # Generate concise visual search concept
            query = extract_concise_keywords(narration_chunk, max_words=4)
            if query in used_queries or len(query.split()) < 2:
                variations = ["view", "detail", "perspective", "environment", "close up", "wide shot", "phenomenon"]
                var_word = variations[i % len(variations)]
                query = f"{query} {var_word}".strip()

            query = query[:45].strip()
            used_queries.add(query)

            scenes.append({
                "scene_number": i + 1,
                "narration": narration_chunk,
                "visual_concept": query,
                "keywords": query.split(),
                "start": round(scene_start, 3),
                "end": round(scene_end, 3),
                "duration": duration,
                "preferred_media_type": "image"
            })

        logger.info(f"[SceneTiming] Derived {len(scenes)} visual scene timings from master word timeline.")
        return scenes
