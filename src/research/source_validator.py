from typing import Dict, Any, Tuple
from src.utils.text_utils import extract_meaningful_tokens, token_similarity

class SourceValidator:
    """Validates research sources for relevance, length, and quality."""

    def validate_source(self, topic_name: str, page_data: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Validate source relevance and content length.
        Returns (is_valid, score, reason).
        """
        if not page_data or not page_data.get("extract"):
            return False, 0.0, "Empty page extract"

        extract = page_data["extract"]
        title = page_data.get("title", "")

        if len(extract.strip()) < 100:
            return False, 0.0, f"Extract too short ({len(extract.strip())} chars)"

        # Calculate topic vs title + extract token similarity
        topic_tokens = extract_meaningful_tokens(topic_name)
        combined_source_text = f"{title} {extract[:500]}"
        source_tokens = extract_meaningful_tokens(combined_source_text)

        if not topic_tokens:
            return True, 0.5, "Topic has no specific tokens"

        intersection = topic_tokens.intersection(source_tokens)
        if not intersection:
            return False, 0.0, "No overlapping topic keywords in source"

        score = len(intersection) / float(len(topic_tokens))
        title_sim = token_similarity(topic_name, title)
        score = max(score, title_sim)

        if score < 0.25:
            return False, score, f"Low topic relevance score ({score:.2f})"

        return True, score, "Source valid and relevant"
