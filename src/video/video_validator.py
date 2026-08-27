from pathlib import Path
from typing import Tuple, Dict, Any
from src.utils.ffmpeg_utils import inspect_media_file

class VideoValidator:
    """Validates final generated video MP4 file for production QA standards."""

    def validate_video(self, video_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate final output MP4.
        Returns (is_valid, reason, info).
        """
        path = Path(video_path)
        if not path.exists():
            return False, "PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Video file does not exist", {}

        file_size = path.stat().st_size
        if file_size < 100000: # Min 100KB
            return False, f"PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Video file size too small ({file_size} bytes)", {}

        info = inspect_media_file(path)
        if not info.get("valid"):
            return False, "PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Media file corrupt or unreadable", {}

        if not info.get("has_video"):
            return False, "PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Video stream missing", {}

        if not info.get("has_audio"):
            return False, "PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Audio stream missing", {}

        duration = info.get("duration", 0.0)
        if duration <= 0.0:
            return False, "PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Video duration is zero", {}

        width = info.get("width", 0)
        height = info.get("height", 0)
        if width > 0 and height > 0:
            if width > height:
                return False, f"PIPELINE BLOCKED — VIDEO VALIDATION FAILURE: Video is horizontal ({width}x{height}), expected vertical 1080x1920", {}

        return True, "Video validation passed", {
            "file_size": file_size,
            "duration": duration,
            "width": width,
            "height": height,
            "has_audio": True
        }
