import pytest
from datetime import datetime, timedelta
from pathlib import Path
from src.database.history_manager import HistoryManager
from src.utils.text_utils import normalize_text, compute_fingerprint, token_similarity

@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_history.sqlite"
    return HistoryManager(db_file)

def test_db_initialization(temp_db: HistoryManager):
    assert temp_db.db_path.exists()
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    assert "topics" in tables
    assert "pipeline_runs" in tables

def test_fresh_topic_cooldown(temp_db: HistoryManager):
    topic = "The Mysterious Ocean Abyss"
    assert not temp_db.is_topic_on_cooldown(topic, cooldown_days=14)

def test_recorded_topic_cooldown(temp_db: HistoryManager):
    topic = "The Mysterious Ocean Abyss"
    temp_db.record_topic_usage(topic, category="Nature & Earth")
    assert temp_db.is_topic_on_cooldown(topic, cooldown_days=14)

def test_case_insensitive_cooldown(temp_db: HistoryManager):
    topic_lower = "why do cats purr"
    topic_upper = "WHY DO CATS PURR"
    temp_db.record_topic_usage(topic_lower, category="Animals")
    assert temp_db.is_topic_on_cooldown(topic_upper, cooldown_days=14)

def test_token_similarity_cooldown(temp_db: HistoryManager):
    topic_orig = "Why Black Holes Swallowing Giant Stars Confuses Scientists"
    topic_similar = "Why Black Hole Swallowing Giant Star Confuses Scientists"
    temp_db.record_topic_usage(topic_orig, category="Space")
    assert temp_db.is_topic_on_cooldown(topic_similar, cooldown_days=14)

def test_expired_cooldown(temp_db: HistoryManager):
    topic = "Ancient Glaciers of Iceland"
    fingerprint = compute_fingerprint(topic)
    old_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
    
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO topics (topic_name, category, fingerprint, used_at) VALUES (?, ?, ?, ?)",
            (topic, "Geography", fingerprint, old_date)
        )
        conn.commit()
        
    assert not temp_db.is_topic_on_cooldown(topic, cooldown_days=14)

def test_null_used_at_eligible(temp_db: HistoryManager):
    topic = "Unused Generated Candidate"
    fingerprint = compute_fingerprint(topic)
    
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO topics (topic_name, category, fingerprint, used_at) VALUES (?, ?, ?, NULL)",
            (topic, "Science", fingerprint)
        )
        conn.commit()
        
    assert not temp_db.is_topic_on_cooldown(topic, cooldown_days=14)
