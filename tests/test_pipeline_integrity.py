import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.database.history_manager import HistoryManager
from src.topic.topic_selector import TopicSelector
from src.media.media_manager import MediaManager
from src.media.visual_provider import ProviderHealthManager
from src.audio.music_manager import MusicManager
from src.video.video_builder import VideoBuilder
from src.video.video_validator import VideoValidator
from src.audio.voice_generator import VoiceGenerator
from src.media.fallback_assets import FallbackAssetsManager

@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "integrity_test_history.sqlite"
    return HistoryManager(db_file)

def test_provider_failure_recovery_and_isolation(tmp_path: Path):
    """Test that network failures on one provider mark it unavailable without breaking pipeline."""
    mm = MediaManager(temp_dir=tmp_path)
    
    # Simulate network error on Wikimedia HTTP requests
    with patch("requests.get", side_effect=Exception("DNS lookup failed")):
        scenes = mm.source_scene_visuals("Deep space black hole event horizon phenomenon.", "Black Hole Event")
        assert len(scenes) >= 5
        # Wikimedia should be marked disabled after failure threshold
        assert not mm.health_manager.is_available("wikimedia")
        # All scenes still got valid fallback assets
        for sc in scenes:
            assert Path(sc["asset_path"]).exists()

def test_missing_music_non_blocking(tmp_path: Path):
    """Test that missing music directory or files does NOT block video build."""
    empty_dir = tmp_path / "no_music"
    music_mgr = MusicManager(music_dir=empty_dir)
    music_info = music_mgr.select_background_music()
    assert music_info is None
    
    # Build video without music
    builder = VideoBuilder(output_dir=tmp_path / "vids", temp_dir=tmp_path / "tmp")
    fallback = FallbackAssetsManager(tmp_path / "fb")
    scenes = []
    for i in range(1, 6):
        asset = tmp_path / f"sc_{i}.png"
        meta = fallback.get_fallback_asset(i, "nature", asset)
        scenes.append({"scene_number": i, "visual_concept": "nature", "asset_path": str(asset), "asset_metadata": meta})
        
    vg = VoiceGenerator()
    narr_file = tmp_path / "narr.mp3"
    v_data = vg.generate_voice("Sample narration without background music track.", narr_file)
    
    out_mp4 = builder.build_short_video(
        topic_name="No Music Test",
        scenes=scenes,
        narration_path=narr_file,
        narration_duration=v_data["duration"],
        music_info=None,
        output_filename="no_music.mp4"
    )
    assert out_mp4.exists()

def test_candidate_exhaustion_batch_recovery(temp_db: HistoryManager):
    """Test that candidate generator advances batches when initial pool is exhausted."""
    selector = TopicSelector(temp_db, cooldown_days=14)
    # Block first batch candidates in DB
    batch1 = selector.generator.generate_candidates(count=60, seed_offset=0)
    for c in batch1:
        temp_db.record_topic_usage(c["topic_name"], c["category"])
        
    # Selection should advance to batch 2 and find fresh candidate
    fresh_topic = selector.select_topic(max_batches=5)
    assert fresh_topic is not None
    assert not temp_db.is_topic_on_cooldown(fresh_topic["topic_name"], cooldown_days=14)
