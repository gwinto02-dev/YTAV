from pathlib import Path
from typing import Tuple, Dict, Any
from src.utils.ffmpeg_utils import inspect_media_file

class AudioValidator:
    """Validates generated narration and music audio files."""

    def validate_audio(self, audio_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate audio file presence, size, and duration.
        Returns (is_valid, reason, info).
        """
        path = Path(audio_path)
        if not path.exists():
            return False, "Audio file does not exist", {}

        if path.stat().st_size < 100:
            return False, f"Audio file size too small ({path.stat().st_size} bytes)", {}

        info = inspect_media_file(path)
        if not info.get("valid") or not info.get("has_audio"):
            return False, "Invalid or unreadable audio stream", {}

        duration = info.get("duration", 0.0)
        if duration <= 0.0:
            return False, "Audio duration is zero", {}

        return True, "Audio valid", {"duration": duration, "file_size": path.stat().st_size}
