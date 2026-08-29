import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.utils.text_utils import normalize_text, compute_fingerprint, token_similarity
from src.utils.logger import logger

class HistoryManager:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema if not present."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_name TEXT NOT NULL,
                category TEXT NOT NULL,
                fingerprint TEXT UNIQUE NOT NULL,
                used_at DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                script_text TEXT NOT NULL,
                word_count INTEGER,
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id) REFERENCES topics(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                title_text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id) REFERENCES topics(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                hook_text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(topic_id) REFERENCES topics(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error_reason TEXT,
                output_video_path TEXT,
                youtube_video_id TEXT,
                youtube_url TEXT,
                run_metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("PRAGMA table_info(pipeline_runs)")
            cols = [r["name"] for r in cursor.fetchall()]
            if "youtube_video_id" not in cols:
                cursor.execute("ALTER TABLE pipeline_runs ADD COLUMN youtube_video_id TEXT")
            if "youtube_url" not in cols:
                cursor.execute("ALTER TABLE pipeline_runs ADD COLUMN youtube_url TEXT")

            conn.commit()


    def is_topic_on_cooldown(self, topic_name: str, cooldown_days: int = 14) -> bool:
        """
        Check if topic (or near duplicate) was used within the cooldown window.
        Returns True if topic is ON COOLDOWN (i.e. ineligible).
        """
        norm_input = normalize_text(topic_name)
        input_fingerprint = compute_fingerprint(topic_name)
        cutoff_date = (datetime.now() - timedelta(days=cooldown_days)).strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Fetch all topics that have been used within cooldown_days
            cursor.execute(
                """
                SELECT topic_name, fingerprint, used_at FROM topics
                WHERE used_at IS NOT NULL AND used_at >= ?
                """,
                (cutoff_date,)
            )
            used_records = cursor.fetchall()

        for rec in used_records:
            # 1. Exact fingerprint match
            if rec["fingerprint"] == input_fingerprint:
                return True
            
            # 2. Normalized string equality
            norm_rec = normalize_text(rec["topic_name"])
            if norm_rec == norm_input:
                return True
            
            # 3. High token similarity match (prevent rephrased duplicates)
            if token_similarity(topic_name, rec["topic_name"]) >= 0.75:
                return True

        return False

    def record_topic_usage(
        self,
        topic_name: str,
        category: str,
        script_text: str = "",
        title: str = "",
        hook: str = ""
    ) -> int:
        """
        Record a topic as USED in the database.
        This must ONLY be called when a topic is chosen for a real production run and passed QA.
        """
        fingerprint = compute_fingerprint(topic_name)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if topic entry already exists
            cursor.execute("SELECT id FROM topics WHERE fingerprint = ?", (fingerprint,))
            row = cursor.fetchone()

            if row:
                topic_id = row["id"]
                cursor.execute(
                    "UPDATE topics SET used_at = ?, category = ? WHERE id = ?",
                    (now_str, category, topic_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO topics (topic_name, category, fingerprint, used_at) VALUES (?, ?, ?, ?)",
                    (topic_name, category, fingerprint, now_str)
                )
                topic_id = cursor.lastrowid

            # Save script details if provided
            if script_text:
                words = len(script_text.split())
                cursor.execute(
                    "INSERT INTO scripts (topic_id, script_text, word_count, title) VALUES (?, ?, ?, ?)",
                    (topic_id, script_text, words, title)
                )

            if title:
                cursor.execute(
                    "INSERT INTO titles (topic_id, title_text) VALUES (?, ?)",
                    (topic_id, title)
                )

            if hook:
                cursor.execute(
                    "INSERT INTO hooks (topic_id, hook_text) VALUES (?, ?)",
                    (topic_id, hook)
                )

            conn.commit()
            logger.info(f"Recorded topic usage in history DB: '{topic_name}' (ID: {topic_id})")
            return topic_id

    def record_pipeline_run(
        self,
        topic_name: str,
        status: str,
        error_reason: Optional[str] = None,
        video_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        youtube_video_id: Optional[str] = None,
        youtube_url: Optional[str] = None
    ) -> int:
        """Record pipeline execution status and summary."""
        meta_str = json.dumps(metadata) if metadata else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pipeline_runs (
                    topic_name, status, error_reason, output_video_path,
                    youtube_video_id, youtube_url, run_metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (topic_name, status, error_reason, video_path, youtube_video_id, youtube_url, meta_str)
            )
            conn.commit()
            return cursor.lastrowid


    def get_recent_topics(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of recently used topics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM topics WHERE used_at IS NOT NULL ORDER BY used_at DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
