import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from src.utils.logger import logger

def get_ffmpeg_path() -> str:
    """Find FFmpeg executable path."""
    # Check if system has ffmpeg in PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    # Try imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception as e:
        logger.debug(f"imageio_ffmpeg lookup failed: {e}")
        
    raise RuntimeError("FFmpeg executable not found on system or via imageio-ffmpeg.")

def run_ffmpeg_cmd(cmd_args: list, timeout: int = 120) -> subprocess.CompletedProcess:
    """
    Run an FFmpeg command list safely.
    """
    ffmpeg_exe = get_ffmpeg_path()
    full_cmd = [ffmpeg_exe] + cmd_args
    
    logger.debug(f"Running FFmpeg command: {' '.join(full_cmd)}")
    
    result = subprocess.run(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout
    )
    
    if result.returncode != 0:
        logger.error(f"FFmpeg command failed with code {result.returncode}:\n{result.stderr[-1000:]}")
        raise RuntimeError(f"FFmpeg command failed: {result.stderr[-500:]}")
        
    return result

def inspect_media_file(file_path: Path) -> Dict[str, Any]:
    """
    Inspect media file using FFmpeg to verify streams, resolution, and duration.
    """
    if not file_path.exists():
        return {"valid": False, "reason": "File does not exist"}
        
    if file_path.stat().st_size == 0:
        return {"valid": False, "reason": "File size is zero"}

    # Run FFmpeg info command (reading input without output)
    cmd = ["-hide_banner", "-i", str(file_path)]
    ffmpeg_exe = get_ffmpeg_path()
    proc = subprocess.run([ffmpeg_exe] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr = proc.stderr
    
    has_video = "Video:" in stderr
    has_audio = "Audio:" in stderr
    
    # Extract duration from stderr output if available (e.g. Duration: 00:00:45.20)
    duration = 0.0
    import re
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
    if dur_match:
        h, m, s = dur_match.groups()
        duration = float(h)*3600 + float(m)*60 + float(s)
        
    # Extract resolution if video stream present (e.g. 1080x1920)
    width, height = 0, 0
    res_match = re.search(r"Video:.*?,\s*(\d{3,4})x(\d{3,4})", stderr)
    if res_match:
        width, height = int(res_match.group(1)), int(res_match.group(2))
        
    return {
        "valid": True,
        "file_size": file_path.stat().st_size,
        "has_video": has_video,
        "has_audio": has_audio,
        "duration": duration,
        "width": width,
        "height": height,
        "raw_info": stderr
    }
