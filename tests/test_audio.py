import pytest
from pathlib import Path
from src.audio.voice_generator import VoiceGenerator
from src.audio.audio_validator import AudioValidator
from src.captions.caption_generator import CaptionGenerator
from src.audio.music_manager import MusicManager

def test_voice_generator_test_mode(tmp_path: Path):
    vg = VoiceGenerator()
    out_file = tmp_path / "narration.mp3"
    res = vg.generate_voice("Imagine discovering that bioluminescent ocean waves glow bright blue in the dark night ocean.", out_file)
    
    assert out_file.exists()
    assert res["duration"] > 0.0
    
    val = AudioValidator()
    is_valid, reason, info = val.validate_audio(out_file)
    assert is_valid

def test_caption_generator(tmp_path: Path):
    cg = CaptionGenerator()
    script = "Imagine discovering a phenomenon so strange that scientists still struggle to explain it."
    out_srt = tmp_path / "captions.srt"
    res = cg.generate_srt_captions(script, duration=20.0, output_path=out_srt)
    
    assert out_srt.exists()
    assert res["chunk_count"] > 0
    content = out_srt.read_text(encoding="utf-8")
    assert "-->" in content
    assert "IMAGINE DISCOVERING" in content

def test_karaoke_ass_caption_generator(tmp_path: Path):
    from src.timeline.timeline_builder import TimelineBuilder
    tb = TimelineBuilder()
    cg = CaptionGenerator()
    script = "Did you know that octopuses have three hearts?"
    timeline = tb.build_master_timeline(script, "Octopus", total_audio_duration=4.0)
    out_ass = tmp_path / "captions.ass"
    
    res = cg.generate_karaoke_ass_captions(timeline, out_ass)
    assert out_ass.exists()
    assert res["event_count"] > 0
    content = out_ass.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "[V4+ Styles]" in content
    assert "Dialogue:" in content
    assert "{\\c&H0000FFFF&}" in content  # Active word highlight color

def test_music_manager_empty_dir_fallback(tmp_path: Path):
    empty_music_dir = tmp_path / "empty_music"
    empty_music_dir.mkdir()
    mm = MusicManager(music_dir=empty_music_dir)
    res = mm.select_background_music()
    assert res is None # Gracefully returns None without throwing exception
