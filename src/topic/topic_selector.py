from typing import Dict, Any, Optional
from src.topic.topic_generator import TopicGenerator
from src.topic.topic_validator import TopicValidator
from src.database.history_manager import HistoryManager
from src.utils.text_utils import compute_fingerprint
from src.utils.logger import logger

class TopicSelector:
    """Orchestrates topic selection with multi-tier exhaustion protection."""
    
    def __init__(self, history_manager: HistoryManager, cooldown_days: int = 14):
        self.history_manager = history_manager
        self.generator = TopicGenerator()
        self.validator = TopicValidator(history_manager, cooldown_days=cooldown_days)

    def select_topic(self, max_batches: int = 10) -> Dict[str, Any]:
        """
        Select a valid, unique, non-cooldown topic.
        Does NOT record usage in history DB (usage recorded post content QA).
        """
        logger.info("Selecting unique topic...")
        
        for batch_idx in range(max_batches):
            candidates = self.generator.generate_candidates(count=60, seed_offset=batch_idx * 100)
            logger.debug(f"Generated candidate batch {batch_idx + 1}/{max_batches} ({len(candidates)} candidates)")
            
            for candidate in candidates:
                topic_name = candidate["topic_name"]
                category = candidate["category"]
                
                is_valid, reason = self.validator.validate_topic(topic_name, category)
                if is_valid:
                    fingerprint = compute_fingerprint(topic_name)
                    logger.info(f"Selected Topic: '{topic_name}' [{category}]")
                    return {
                        "topic_name": topic_name,
                        "category": category,
                        "fingerprint": fingerprint
                    }
                else:
                    logger.debug(f"Rejected candidate '{topic_name}': {reason}")
                    
        raise RuntimeError(f"Exhausted {max_batches} candidate batches without finding an eligible topic.")
