from pathlib import Path
from typing import Dict, Any, List
from config.settings import (
    CAPTION_FONT_SIZE, CAPTION_FONT_FAMILY, CAPTION_PRIMARY_COLOR,
    CAPTION_HIGHLIGHT_COLOR, CAPTION_OUTLINE_COLOR, CAPTION_OUTLINE_THICKNESS,
    CAPTION_SHADOW, CAPTION_VERTICAL_POSITION
)
from src.utils.logger import logger

class CaptionGenerator:
    """Generates modern YouTube Shorts / TikTok karaoke-style ASS subtitles with word-by-word highlighting."""

    def generate_karaoke_ass_captions(
        self,
        master_timeline: Dict[str, Any],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        Generate ASS subtitle file with animated word-by-word karaoke highlighting from master timeline.
        """
        logger.info("[Captions] Generating karaoke ASS subtitles with word-level highlighting...")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        caption_groups = master_timeline.get("caption_groups", [])
        
        # Build ASS file header and style specs
        ass_lines = [
            "[Script Info]",
            "Title: Shorts Karaoke Subtitles",
            "ScriptType: v4.00+",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{CAPTION_FONT_FAMILY},{CAPTION_FONT_SIZE},{CAPTION_PRIMARY_COLOR},{CAPTION_HIGHLIGHT_COLOR},{CAPTION_OUTLINE_COLOR},&H80000000,-1,0,0,0,100,100,0,0,1,{CAPTION_OUTLINE_THICKNESS},{CAPTION_SHADOW},2,50,50,{CAPTION_VERTICAL_POSITION},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        total_dialogue_events = 0

        for group in caption_groups:
            words = group.get("words", [])
            if not words:
                continue

            # Generate individual word highlight state events for this phrase group
            for idx, curr_w in enumerate(words):
                w_start = curr_w["start"]
                w_end = curr_w["end"]

                # If last word in group, extend display to next group start or group end
                if idx == len(words) - 1 and idx < len(words):
                    w_end = max(w_end, group["end"])

                start_ts = self._format_ass_timestamp(w_start)
                end_ts = self._format_ass_timestamp(w_end)

                # Format phrase with current active word highlighted
                styled_words = []
                for w_i, word_item in enumerate(words):
                    raw_w = word_item["word"].upper()
                    if w_i == idx:
                        # Active word receives strong highlight color override
                        styled_words.append(f"{{\\c{CAPTION_HIGHLIGHT_COLOR}&}}{raw_w}{{\\c{CAPTION_PRIMARY_COLOR}&}}")
                    else:
                        styled_words.append(raw_w)

                formatted_line = " ".join(styled_words)
                dialogue = f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{formatted_line}"
                ass_lines.append(dialogue)
                total_dialogue_events += 1

        output_path.write_text("\n".join(ass_lines), encoding="utf-8")
        logger.info(f"[Captions] Generated ASS karaoke subtitle file: {output_path.name} ({total_dialogue_events} timing events)")

        return {
            "ass_path": str(output_path),
            "event_count": total_dialogue_events,
            "group_count": len(caption_groups)
        }

    def generate_srt_captions(self, script_text: str, duration: float, output_path: Path) -> Dict[str, Any]:
        """Fallback SRT subtitle generator for legacy calls."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        words = script_text.strip().split()
        chunks = [" ".join(words[i:i + 4]) for i in range(0, len(words), 4)]
        time_per_chunk = duration / float(len(chunks)) if chunks else 1.0

        srt_lines = []
        for idx, text in enumerate(chunks, 1):
            start_sec = (idx - 1) * time_per_chunk
            end_sec = idx * time_per_chunk
            srt_lines.append(f"{idx}\n{self._format_srt_timestamp(start_sec)} --> {self._format_srt_timestamp(end_sec)}\n{text.upper()}\n")

        output_path.write_text("\n".join(srt_lines), encoding="utf-8")
        return {"srt_path": str(output_path), "chunk_count": len(chunks)}

    def _format_ass_timestamp(self, seconds: float) -> str:
        """Format seconds to ASS timestamp: H:MM:SS.cs (centiseconds)"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        if cs >= 100:
            secs += 1
            cs -= 100
        return f"{hrs:01d}:{mins:02d}:{secs:02d}.{cs:02d}"

    def _format_srt_timestamp(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
