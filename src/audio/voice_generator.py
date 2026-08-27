import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional
import edge_tts
from config.settings import VOICE_NAME, TEST_MODE, TEMP_DIR
from src.utils.ffmpeg_utils import inspect_media_file
from src.utils.logger import logger

class VoiceGenerator:
    """Generates neural narration voiceover using Edge-TTS with offline fallback."""

    def __init__(self, voice_name: str = VOICE_NAME):
        self.voice_name = voice_name

    def generate_voice(self, script_text: str, output_path: Path) -> Dict[str, Any]:
        """
        Generate narration audio file from script text.
        """
        logger.info(f"Generating voice narration using voice '{self.voice_name}'...")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        boundary_events = []
        if TEST_MODE:
            self._create_test_audio(script_text, output_path)
        else:
            try:
                boundary_events = asyncio.run(self._generate_edge_tts(script_text, output_path))
            except Exception as e:
                logger.warning(f"Edge-TTS generation failed: {e}. Using offline synthetic audio fallback.")
                self._create_test_audio(script_text, output_path)

        # Inspect generated audio file
        info = inspect_media_file(output_path)
        duration = info.get("duration", 0.0)
        if duration <= 0.0:
            # Estimate duration based on word count (~140 words per minute = 2.33 words/sec)
            words = len(script_text.split())
            duration = max(20.0, words / 2.33)

        logger.info(f"Voice narration generated successfully (Duration: {duration:.2f}s, Path: {output_path.name})")

        return {
            "audio_path": str(output_path),
            "duration": duration,
            "voice_name": self.voice_name,
            "script_text": script_text,
            "boundary_events": boundary_events
        }

    async def _generate_edge_tts(self, text: str, output_path: Path) -> list:
        communicate = edge_tts.Communicate(text, self.voice_name)
        events = []
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("SentenceBoundary", "WordBoundary"):
                    events.append(chunk)
        return events

    def _create_test_audio(self, text: str, output_path: Path):
        """Generate synthetic silence/beep audio file using FFmpeg for test mode."""
        words = len(text.split())
        est_duration = max(10, int(words / 2.5))
        
        from src.utils.ffmpeg_utils import get_ffmpeg_path, subprocess
        cmd = [
            get_ffmpeg_path(), "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
            "-t", str(est_duration),
            "-q:a", "9", "-acodec", "libmp3lame", str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
