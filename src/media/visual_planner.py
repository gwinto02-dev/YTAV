import re
from typing import List, Dict, Any
from src.utils.text_utils import extract_concise_keywords, extract_meaningful_tokens
from src.utils.logger import logger

class VisualPlanner:
    """Plans 5-8 scenes per Short with concise 2-6 word visual search queries."""

    def plan_visuals(self, script_text: str, topic_name: str, target_duration: float = 45.0) -> List[Dict[str, Any]]:
        """
        Divide script into 5-8 scenes with concise visual search concepts.
        """
        logger.info("Planning visual scenes...")
        
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script_text) if len(s.strip()) > 10]
        if not sentences:
            sentences = [script_text]

        # Group sentences into 5-8 scenes
        total_scenes = max(5, min(8, len(sentences)))
        sentences_per_scene = max(1, len(sentences) // total_scenes)

        scenes = []
        used_queries = set()
        topic_keywords = extract_concise_keywords(topic_name, max_words=3)

        for i in range(total_scenes):
            start_idx = i * sentences_per_scene
            if i == total_scenes - 1:
                scene_sentences = sentences[start_idx:]
            else:
                scene_sentences = sentences[start_idx:start_idx + sentences_per_scene]

            narration_chunk = " ".join(scene_sentences)
            if not narration_chunk:
                narration_chunk = script_text[:100]

            # Generate concise 2-5 word visual query
            query = extract_concise_keywords(narration_chunk, max_words=4)
            
            # Deduplicate query
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
                "preferred_media_type": "image"
            })

        logger.info(f"Planned {len(scenes)} visual scenes with concise queries.")
        return scenes
