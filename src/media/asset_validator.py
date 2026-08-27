from pathlib import Path
from typing import Tuple, Dict, Any
from PIL import Image
from src.utils.ffmpeg_utils import inspect_media_file

class AssetValidator:
    """Validates downloaded visual media files for size, readability, and dimensions."""

    def validate_asset(self, file_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate image or video asset file.
        Returns (is_valid, reason, metadata).
        """
        path = Path(file_path)
        if not path.exists():
            return False, "File does not exist", {}

        if path.stat().st_size < 1000:
            return False, f"File size too small ({path.stat().st_size} bytes)", {}

        # First try PIL for image format
        try:
            with Image.open(path) as img:
                img.verify()
            with Image.open(path) as img:
                w, h = img.size
                return True, "Valid image", {"type": "image", "width": w, "height": h}
        except Exception:
            pass

        # Try FFmpeg for video media
        info = inspect_media_file(path)
        if info.get("valid") and info.get("has_video"):
            return True, "Valid video", {
                "type": "video",
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "duration": info.get("duration", 0.0)
            }

        return False, "Unreadable or corrupted media file", {}
