from typing import Dict, Any, Tuple
from src.qa.deterministic_qa import DeterministicQA

class ContentQA:
    """Wrapper for Content Quality Assurance validation."""

    def __init__(self, history_manager):
        self.d_qa = DeterministicQA(history_manager)

    def validate_content_package(
        self,
        topic_data: Dict[str, Any],
        research_data: Dict[str, Any],
        script_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate topic, research, and script content prior to video render."""
        is_t_valid, t_reason = self.d_qa.qa_topic(topic_data)
        if not is_t_valid:
            return False, f"Topic Stage QA Failed: {t_reason}"

        is_r_valid, r_reason = self.d_qa.qa_research(research_data)
        if not is_r_valid:
            return False, f"Research Stage QA Failed: {r_reason}"

        is_s_valid, s_reason = self.d_qa.qa_script_and_content(script_data)
        if not is_s_valid:
            return False, f"Script Stage QA Failed: {s_reason}"

        return True, "All Content QA checks passed successfully"
