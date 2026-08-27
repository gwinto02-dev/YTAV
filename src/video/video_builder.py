import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT, TARGET_FPS, VIDEOS_DIR, TEMP_DIR
from src.utils.ffmpeg_utils import get_ffmpeg_path, run_ffmpeg_cmd
from src.utils.logger import logger

class VideoBuilder:
    """FFmpeg-based Video Builder producing 1080x1920 vertical Shorts MP4 synchronized to master timeline."""

    def __init__(self, output_dir: Path = VIDEOS_DIR, temp_dir: Path = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def build_short_video(
        self,
        topic_name: str,
        scenes: List[Dict[str, Any]],
        narration_path: Path,
        narration_duration: float,
        caption_path: Optional[Path] = None,
        music_info: Optional[Dict[str, Any]] = None,
        output_filename: str = "short_video.mp4"
    ) -> Path:
        """
        Build vertical 1080x1920 video with synchronized scene durations, narration audio, captions, and optional music.
        """
        logger.info("[VideoBuilder] Building 1080x1920 vertical MP4 video via FFmpeg...")
        final_mp4 = self.output_dir / output_filename

        # Prepare scene clip inputs
        concat_list_path = self.temp_dir / "concat_scenes.txt"
        scaled_clips = []

        for idx, sc in enumerate(scenes, 1):
            asset_path = Path(sc["asset_path"])
            scene_duration = sc.get("duration", max(2.5, narration_duration / float(len(scenes))))
            scaled_clip = self.temp_dir / f"clip_{idx}.mp4"
            self._create_scene_clip(asset_path, scaled_clip, duration=scene_duration)
            scaled_clips.append(scaled_clip)

        # Write FFmpeg concat text file
        concat_lines = [f"file '{c.resolve().as_posix()}'" for c in scaled_clips]
        concat_list_path.write_text("\n".join(concat_lines), encoding="utf-8")

        # Concat visuals MP4
        concat_mp4 = self.temp_dir / "concat_visuals.mp4"
        cmd_concat = [
            "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path),
            "-c", "copy", str(concat_mp4)
        ]
        run_ffmpeg_cmd(cmd_concat, timeout=120)

        # Final merge: Visuals + Narration + Subtitles + Music
        filter_complex = []
        inputs = ["-i", str(concat_mp4), "-i", str(narration_path)]
        
        audio_map = "1:a"
        if music_info and Path(music_info["music_path"]).exists():
            inputs.extend(["-i", str(music_info["music_path"])])
            filter_complex.append(f"[2:a]volume=0.08[bgm];[1:a][bgm]amix=inputs=2:duration=first[aout]")
            audio_map = "[aout]"

        vf_filters = []
        if caption_path and Path(caption_path).exists():
            # Format windows path for ffmpeg subtitles/ass filter
            escaped_cap = str(Path(caption_path).resolve()).replace("\\", "/").replace(":", "\\:")
            if str(caption_path).endswith(".ass"):
                sub_filter = f"ass='{escaped_cap}'"
            else:
                sub_filter = (
                    f"subtitles='{escaped_cap}':force_style="
                    f"'Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=250'"
                )
            vf_filters.append(sub_filter)

        cmd_final = ["-y"] + inputs
        
        if filter_complex:
            cmd_final.extend(["-filter_complex", ";".join(filter_complex)])
            
        if vf_filters:
            cmd_final.extend(["-vf", ",".join(vf_filters)])

        cmd_final.extend([
            "-map", "0:v",
            "-map", audio_map,
            "-t", str(narration_duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(TARGET_FPS),
            "-c:a", "aac", "-b:a", "192k",
            str(final_mp4)
        ])

        run_ffmpeg_cmd(cmd_final, timeout=180)
        logger.info(f"[VideoBuilder] Video assembly complete! Output saved: {final_mp4.resolve()}")
        return final_mp4

    def _create_scene_clip(self, asset_path: Path, output_clip: Path, duration: float):
        """Create a scaled 1080x1920 clip from image/video asset matching timeline duration."""
        cmd = [
            "-y", "-loop", "1", "-i", str(asset_path),
            "-t", str(duration),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}",
            "-r", str(TARGET_FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(output_clip)
        ]
        run_ffmpeg_cmd(cmd, timeout=60)
