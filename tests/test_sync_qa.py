import pytest
from src.timeline.timeline_builder import TimelineBuilder
from src.qa.sync_qa import SynchronizationQA

def test_synchronization_qa_pass():
    tb = TimelineBuilder()
    sqa = SynchronizationQA()
    script = "Did you know that octopuses have three hearts? They live in the ocean."
    timeline = tb.build_master_timeline(script, "Octopus", total_audio_duration=5.0)
    
    is_valid, reason, metrics = sqa.validate_timeline_and_sync(timeline, video_duration=5.02)
    assert is_valid
    assert metrics["difference"] < 0.1
    assert metrics["words_aligned"] == 13

def test_synchronization_qa_fail_duration_mismatch():
    tb = TimelineBuilder()
    sqa = SynchronizationQA()
    script = "Did you know that octopuses have three hearts?"
    timeline = tb.build_master_timeline(script, "Octopus", total_audio_duration=4.0)
    
    # Simulate video duration off by 2.0s
    is_valid, reason, metrics = sqa.validate_timeline_and_sync(timeline, video_duration=6.0)
    assert not is_valid
    assert "differs" in reason.lower()
