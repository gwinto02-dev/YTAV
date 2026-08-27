import pytest
from pathlib import Path
from unittest.mock import patch
from src.database.history_manager import HistoryManager
from src.topic.topic_selector import TopicSelector
from src.research.research_manager import ResearchManager
from src.script.script_generator import ScriptGenerator
from src.qa.content_qa import ContentQA
from src.media.media_manager import MediaManager
from src.audio.voice_generator import VoiceGenerator
from src.captions.caption_generator import CaptionGenerator
from src.audio.music_manager import MusicManager
from src.video.video_builder import VideoBuilder
from src.video.video_validator import VideoValidator
from src.qa.pipeline_integrity import PipelineIntegrity

def test_full_pipeline_end_to_end(tmp_path: Path):
    """Execute complete end-to-end pipeline test in isolated temp environment."""
    db_file = tmp_path / "test_history.sqlite"
    history_mgr = HistoryManager(db_file)
    content_qa = ContentQA(history_mgr)
    video_val = VideoValidator()
    integrity = PipelineIntegrity(reports_dir=tmp_path / "reports", metadata_dir=tmp_path / "metadata")

    # 1. Topic
    topic_selector = TopicSelector(history_mgr, cooldown_days=14)
    topic_data = topic_selector.select_topic()
    assert topic_data["topic_name"]

    # 2. Research
    research_mgr = ResearchManager()
    research_data = research_mgr.research_topic(topic_data["topic_name"], topic_data["category"])
    assert len(research_data["facts"]) > 0

    # 3. Script
    script_gen = ScriptGenerator()
    script_data = script_gen.generate_script_and_titles(research_data)
    assert 90 <= script_data["word_count"] <= 150

    # 4. Content QA
    is_qa_pass, qa_reason = content_qa.validate_content_package(topic_data, research_data, script_data)
    assert is_qa_pass

    # 5. Voice
    voice_gen = VoiceGenerator()
    audio_out = tmp_path / "temp" / "narr.mp3"
    voice_data = voice_gen.generate_voice(script_data["script_text"], audio_out)
    assert voice_data["duration"] > 0

    # 6. Master Timeline
    from src.timeline.timeline_builder import TimelineBuilder
    tb = TimelineBuilder()
    master_timeline = tb.build_master_timeline(
        script_text=script_data["script_text"],
        topic_name=topic_data["topic_name"],
        total_audio_duration=voice_data["duration"],
        boundary_events=voice_data.get("boundary_events", [])
    )
    assert len(master_timeline["words"]) > 0

    # 7. Karaoke Captions
    caption_gen = CaptionGenerator()
    ass_out = tmp_path / "temp" / "captions.ass"
    caption_meta = caption_gen.generate_karaoke_ass_captions(master_timeline, ass_out)
    assert Path(caption_meta["ass_path"]).exists()

    # 8. Media Sourcing for Timeline Scenes
    media_mgr = MediaManager(temp_dir=tmp_path / "temp")
    scenes = media_mgr.source_scene_visuals(master_timeline["scenes"], topic_data["topic_name"])
    assert len(scenes) >= 5

    # 9. Music
    music_mgr = MusicManager(music_dir=tmp_path / "music")
    music_info = music_mgr.select_background_music()

    # 10. Video Builder
    builder = VideoBuilder(output_dir=tmp_path / "videos", temp_dir=tmp_path / "temp")
    video_path = builder.build_short_video(
        topic_name=topic_data["topic_name"],
        scenes=scenes,
        narration_path=Path(voice_data["audio_path"]),
        narration_duration=voice_data["duration"],
        caption_path=ass_out,
        music_info=music_info,
        output_filename="integration_test.mp4"
    )
    assert video_path.exists()

    # 11. Final Video QA
    is_vid_valid, vid_reason, vid_info = video_val.validate_video(video_path)
    assert is_vid_valid

    # 12. Record Topic Usage Post QA Pass
    topic_id = history_mgr.record_topic_usage(
        topic_name=topic_data["topic_name"],
        category=topic_data["category"],
        script_text=script_data["script_text"],
        title=script_data["selected_title"],
        hook=script_data["hook"]
    )
    assert topic_id > 0

    # 13. Reports & Metadata
    run_report_data = {
        "topic": topic_data["topic_name"],
        "category": topic_data["category"],
        "selected_title": script_data["selected_title"],
        "word_count": script_data["word_count"],
        "narration_duration": voice_data["duration"],
        "video_path": str(video_path.resolve()),
        "sources": research_data["sources"],
        "scenes": scenes,
        "provider_health": media_mgr.health_manager.health_state
    }
    meta_file, report_file = integrity.save_run_report(run_report_data, status="SUCCESS")
    assert meta_file.exists()
    assert report_file.exists()
