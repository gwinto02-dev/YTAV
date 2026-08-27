import pytest
from pathlib import Path
from src.video.video_builder import VideoBuilder
from src.video.video_validator import VideoValidator
from src.media.fallback_assets import FallbackAssetsManager
from src.audio.voice_generator import VoiceGenerator

def test_video_builder_and_validator(tmp_path: Path):
    # Setup temporary builder output
    builder = VideoBuilder(output_dir=tmp_path / "videos", temp_dir=tmp_path / "temp")
    
    # Create test fallback scenes
    fallback = FallbackAssetsManager(tmp_path / "fallback")
    scenes = []
    for i in range(1, 6):
        asset_file = tmp_path / f"scene_{i}.png"
        meta = fallback.get_fallback_asset(i, "space stars", asset_file)
        scenes.append({
            "scene_number": i,
            "visual_concept": "space stars",
            "asset_path": str(asset_file),
            "asset_metadata": meta
        })
        
    # Create test narration audio
    vg = VoiceGenerator()
    narration_file = tmp_path / "narration.mp3"
    voice_data = vg.generate_voice("Testing video builder with synthetic narration audio track.", narration_file)
    
    # Create test ASS captions
    from src.timeline.timeline_builder import TimelineBuilder
    from src.captions.caption_generator import CaptionGenerator
    tb = TimelineBuilder()
    cg = CaptionGenerator()
    timeline = tb.build_master_timeline("Testing video builder with synthetic narration audio track.", "Test Build", voice_data["duration"])
    ass_file = tmp_path / "captions.ass"
    cg.generate_karaoke_ass_captions(timeline, ass_file)

    video_path = builder.build_short_video(
        topic_name="Test Video Build",
        scenes=scenes,
        narration_path=narration_file,
        narration_duration=voice_data["duration"],
        caption_path=ass_file,
        output_filename="test_build.mp4"
    )
    
    assert video_path.exists()
    
    validator = VideoValidator()
    is_valid, reason, info = validator.validate_video(video_path)
    assert is_valid, f"Video validation failed: {reason}"
    assert info["width"] == 1080
    assert info["height"] == 1920
    assert info["has_audio"]
