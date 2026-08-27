import pytest
from src.timeline.word_alignment import WordAlignmentEngine

def test_proportional_word_alignment():
    engine = WordAlignmentEngine()
    script = "Did you know that octopuses have three hearts?"
    words = engine.align_script_words(script, boundary_events=[], total_audio_duration=4.0)
    
    assert len(words) == 8
    assert words[0]["word"] == "Did"
    assert words[0]["start"] == 0.0
    assert words[-1]["end"] <= 4.0
    
    # Check monotonicity
    for i in range(len(words) - 1):
        assert words[i]["end"] <= words[i+1]["start"] + 0.001
        assert words[i]["end"] >= words[i]["start"]

def test_boundary_event_alignment():
    engine = WordAlignmentEngine()
    script = "Did you know that octopuses have three hearts?"
    boundary_events = [
        {"type": "SentenceBoundary", "offset": 1000000, "duration": 30000000, "text": "Did you know that octopuses have three hearts?"}
    ]
    words = engine.align_script_words(script, boundary_events=boundary_events, total_audio_duration=3.5)
    
    assert len(words) == 8
    assert words[0]["start"] >= 0.10
    assert words[-1]["end"] <= 3.5

def test_master_timeline_building():
    from src.timeline.timeline_builder import TimelineBuilder
    builder = TimelineBuilder()
    script = "Did you know that octopuses have three hearts? They live in the ocean."
    timeline = builder.build_master_timeline(script, "Octopus Hearts", total_audio_duration=6.0)
    
    assert timeline["total_duration"] == 6.0
    assert len(timeline["words"]) == 13
    assert len(timeline["caption_groups"]) > 0
    assert len(timeline["scenes"]) >= 5

def test_scene_timing_continuous():
    from src.timeline.timeline_builder import TimelineBuilder
    builder = TimelineBuilder()
    script = "Did you know that octopuses have three hearts? They live in the deep blue ocean. Scientists are fascinated by them."
    timeline = builder.build_master_timeline(script, "Octopus Hearts", total_audio_duration=10.0)
    
    scenes = timeline["scenes"]
    assert scenes[0]["start"] == 0.0
    assert scenes[-1]["end"] == 10.0
    
    # Check scene continuity (no gaps)
    for i in range(len(scenes) - 1):
        assert scenes[i]["end"] == scenes[i+1]["start"]
