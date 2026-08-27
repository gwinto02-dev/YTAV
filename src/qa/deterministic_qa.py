from typing import Dict, Any, Tuple
from src.topic.topic_validator import TopicValidator
from src.script.script_validator import ScriptValidator
from src.audio.audio_validator import AudioValidator
from src.video.video_validator import VideoValidator

class DeterministicQA:
    """Deterministic Quality Assurance suite across all pipeline steps."""

    def __init__(self, history_manager):
        self.topic_val = TopicValidator(history_manager)
        self.script_val = ScriptValidator()
        self.audio_val = AudioValidator()
        self.video_val = VideoValidator()

    def qa_topic(self, topic_data: Dict[str, Any]) -> Tuple[bool, str]:
        topic_name = topic_data.get("topic_name", "")
        category = topic_data.get("category", "")
        return self.topic_val.validate_topic(topic_name, category)

    def qa_research(self, research_data: Dict[str, Any]) -> Tuple[bool, str]:
        sources = research_data.get("sources", [])
        facts = research_data.get("facts", [])
        if not sources:
            return False, "Research QA Failed: No research sources found"
        if not facts:
            return False, "Research QA Failed: No facts extracted"
        return True, "Research QA Passed"

    def qa_script_and_content(self, script_data: Dict[str, Any]) -> Tuple[bool, str]:
        is_valid, reason = self.script_val.validate_script(script_data)
        if not is_valid:
            return False, f"Content QA Failed: {reason}"

        topic_name = script_data.get("topic", "")
        titles = script_data.get("candidate_titles", [])
        t_valid, title_sel, t_reason = self.script_val.validate_and_select_title(topic_name, titles)
        if not t_valid:
            return False, f"Title QA Failed: {t_reason}"

        return True, "Content & Script QA Passed"

    def qa_visuals(self, scenes: list) -> Tuple[bool, str]:
        if not scenes or len(scenes) < 5:
            return False, f"Visual QA Failed: Scene count too low ({len(scenes)})"
        for sc in scenes:
            if "asset_path" not in sc:
                return False, f"Visual QA Failed: Scene {sc.get('scene_number')} missing asset path"
        return True, "Visual QA Passed"
