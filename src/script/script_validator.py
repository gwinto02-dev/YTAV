from typing import Dict, Any, Tuple, List
from config.settings import MIN_WORD_COUNT, MAX_WORD_COUNT
from src.utils.text_utils import normalize_text, extract_meaningful_tokens

GENERIC_BAD_TITLES = [
    "the legend of historical subject", "amazing mystery revealed",
    "top 10 amazing facts", "you won't believe this", "shocking video",
    "insert title here", "sample title"
]

class ScriptValidator:
    """Validates generated script quality, word count bounds, hook presence, and title specificity."""

    def validate_script(self, script_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate script dictionary.
        Returns (is_valid, reason).
        """
        if not script_data or "script_text" not in script_data:
            return False, "Script data is missing script_text"

        text = script_data["script_text"].strip()
        word_count = script_data.get("word_count", len(text.split()))

        if word_count < MIN_WORD_COUNT:
            return False, f"Script word count too low ({word_count} words; min is {MIN_WORD_COUNT})"

        if word_count > MAX_WORD_COUNT:
            return False, f"Script word count too high ({word_count} words; max is {MAX_WORD_COUNT})"

        norm = normalize_text(text)
        if "[insert" in norm or "historical subject" in norm or "amazing fact here" in norm:
            return False, "Script contains placeholder text"

        hook = script_data.get("hook", "")
        if not hook or len(hook.strip()) < 15:
            return False, "Script lacks a compelling Hook"

        return True, "Script valid"

    def validate_and_select_title(self, topic_name: str, titles: List[str]) -> Tuple[bool, str, str]:
        """
        Validate candidate titles and select the strongest non-generic title.
        Returns (is_valid, selected_title, reason).
        """
        if not titles:
            return False, "", "No title candidates provided"

        topic_tokens = extract_meaningful_tokens(topic_name)

        for title in titles:
            t_norm = normalize_text(title)
            if any(bad in t_norm for bad in GENERIC_BAD_TITLES):
                continue
            if len(title.strip()) < 10 or len(title.strip()) > 80:
                continue

            # Check if title contains at least one meaningful token from topic/domain
            t_tokens = extract_meaningful_tokens(title)
            if topic_tokens and not topic_tokens.intersection(t_tokens):
                # Title has no overlap with topic tokens, check if it has meaningful nouns
                if len(t_tokens) < 2:
                    continue

            return True, title, "Title validated and selected"

        return False, titles[0] if titles else "", "No candidate title passed specificity validation"
