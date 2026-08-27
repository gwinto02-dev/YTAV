import random
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import MUSIC_DIR
from src.utils.logger import logger

class MusicManager:
    """Manages optional background music track selection and volume scaling."""

    def __init__(self, music_dir: Path = MUSIC_DIR):
        self.music_dir = Path(music_dir)

    def select_background_music(self) -> Optional[Dict[str, Any]]:
        """
        Scan music directory and return selected background music track metadata.
        Returns None gracefully if no music files exist (non-blocking).
        """
        if not self.music_dir.exists():
            logger.info("Music directory does not exist. Video will build without background music.")
            return None

        tracks = [
            f for f in self.music_dir.iterdir()
            if f.is_file() and f.suffix.lower() in [".mp3", ".wav", ".m4a", ".aac", ".ogg"]
        ]

        if not tracks:
            logger.info("No music tracks found in assets/music/. Video will build without background music.")
            return None

        selected_track = random.choice(tracks)
        logger.info(f"Selected background music track: '{selected_track.name}'")

        return {
            "music_path": str(selected_track),
            "volume_db": -22.0,  # Low background volume relative to voice
            "volume_filter": "volume=0.08"
        }
