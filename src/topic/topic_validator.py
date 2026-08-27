from typing import Tuple
from src.topic.topic_generator import CATEGORIES
from src.database.history_manager import HistoryManager
from src.utils.text_utils import normalize_text

BAD_PLACEHOLDERS = [
    "[insert", "historical subject", "amazing fact here", "placeholder",
    "undefined", "none", "sample topic", "test topic"
]

class TopicValidator:
    def __init__(self, history_manager: HistoryManager, cooldown_days: int = 14):
        self.history_manager = history_manager
        self.cooldown_days = cooldown_days

    def validate_topic(self, topic_name: str, category: str) -> Tuple[bool, str]:
        """
        Validate topic name syntax, length, placeholders, category, and cooldown status.
        Returns (is_valid, reason).
        """
        if not topic_name or not topic_name.strip():
            return False, "Topic name is empty"
            
        topic_str = topic_name.strip()
        if len(topic_str) < 15:
            return False, f"Topic too short ({len(topic_str)} chars)"
            
        if len(topic_str) > 120:
            return False, f"Topic too long ({len(topic_str)} chars)"

        if category not in CATEGORIES:
            return False, f"Invalid category: {category}"

        norm = normalize_text(topic_str)
        for ph in BAD_PLACEHOLDERS:
            if ph in norm:
                return False, f"Topic contains invalid placeholder pattern: '{ph}'"

        # Check cooldown status in history DB
        if self.history_manager.is_topic_on_cooldown(topic_str, cooldown_days=self.cooldown_days):
            return False, f"Topic '{topic_str}' is on cooldown ({self.cooldown_days} days)"

        return True, "Valid topic"
