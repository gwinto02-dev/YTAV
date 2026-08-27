import pytest
from pathlib import Path
from src.database.history_manager import HistoryManager
from src.topic.topic_generator import TopicGenerator, PHENOMENA, TEMPLATES
from src.topic.topic_validator import TopicValidator
from src.topic.topic_selector import TopicSelector

@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_topic_history.sqlite"
    return HistoryManager(db_file)

def test_topic_generator_candidates():
    gen = TopicGenerator()
    candidates = gen.generate_candidates(count=30, seed_offset=1)
    assert len(candidates) >= 30
    for c in candidates:
        assert "topic_name" in c
        assert "category" in c

def test_candidate_generation_no_db_pollution(temp_db: HistoryManager):
    """Verify that candidate generation does NOT write usage to DB history."""
    selector = TopicSelector(temp_db, cooldown_days=14)
    # Generate candidates
    candidates = selector.generator.generate_candidates(count=50)
    # DB topics table should remain empty
    recent = temp_db.get_recent_topics()
    assert len(recent) == 0

def test_topic_selection_fresh(temp_db: HistoryManager):
    selector = TopicSelector(temp_db, cooldown_days=14)
    selected = selector.select_topic()
    assert "topic_name" in selected
    assert "category" in selected
    assert "fingerprint" in selected

def test_cooldown_rejection(temp_db: HistoryManager):
    selector = TopicSelector(temp_db, cooldown_days=14)
    topic1 = selector.select_topic()
    
    # Record usage in DB
    temp_db.record_topic_usage(topic1["topic_name"], topic1["category"])
    
    # Select next topic - must NOT be topic1
    topic2 = selector.select_topic()
    assert topic2["topic_name"] != topic1["topic_name"]

def test_exhaustion_recovery_with_large_history(temp_db: HistoryManager):
    """Simulate a large history database where many initial candidates are on cooldown."""
    selector = TopicSelector(temp_db, cooldown_days=14)
    
    # Fill DB with first 40 combinations
    count = 0
    for cat, items in PHENOMENA.items():
        for item in items:
            for tmpl in TEMPLATES:
                topic_name = tmpl.format(phenomenon=item)
                temp_db.record_topic_usage(topic_name, cat)
                count += 1
                if count >= 80:
                    break
            if count >= 80:
                break
        if count >= 80:
            break
            
    # System should still successfully find a non-cooldown topic from subsequent candidates
    selected = selector.select_topic(max_batches=10)
    assert selected is not None
    assert not temp_db.is_topic_on_cooldown(selected["topic_name"], cooldown_days=14)

def test_multiple_consecutive_selections(temp_db: HistoryManager):
    selector = TopicSelector(temp_db, cooldown_days=14)
    seen = set()
    for _ in range(5):
        selected = selector.select_topic()
        assert selected["topic_name"] not in seen
        seen.add(selected["topic_name"])
        # Simulate recording usage after pipeline run
        temp_db.record_topic_usage(selected["topic_name"], selected["category"])
