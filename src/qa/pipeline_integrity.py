import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
from config.settings import REPORTS_DIR, METADATA_DIR
from src.utils.logger import logger

class PipelineIntegrity:
    """Manages pipeline report logging, metadata serialization, and output saving."""

    def __init__(self, reports_dir: Path = REPORTS_DIR, metadata_dir: Path = METADATA_DIR):
        self.reports_dir = Path(reports_dir)
        self.metadata_dir = Path(metadata_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_run_report(self, run_data: Dict[str, Any], status: str = "SUCCESS") -> Tuple[Path, Path]:
        """Save JSON metadata and human-readable Markdown report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = run_data.get("topic", "run").lower().replace(" ", "_")[:30]
        
        meta_file = self.metadata_dir / f"metadata_{timestamp}_{topic_slug}.json"
        report_file = self.reports_dir / f"report_{timestamp}_{topic_slug}.md"

        # Save metadata JSON
        run_metadata = {
            "timestamp": timestamp,
            "status": status,
            "topic": run_data.get("topic"),
            "category": run_data.get("category"),
            "selected_title": run_data.get("selected_title"),
            "word_count": run_data.get("word_count"),
            "narration_duration": run_data.get("narration_duration"),
            "video_path": run_data.get("video_path"),
            "sources": run_data.get("sources", []),
            "scenes": run_data.get("scenes", []),
            "provider_health": run_data.get("provider_health", {})
        }

        meta_file.write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")

        # Save Markdown Report
        md_content = f"""# Pipeline Execution Report

- **Status:** `{status}`
- **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Topic:** {run_data.get('topic')}
- **Category:** {run_data.get('category')}
- **Title:** {run_data.get('selected_title')}
- **Word Count:** {run_data.get('word_count')} words
- **Duration:** {run_data.get('narration_duration', 0.0):.2f} seconds
- **Output Video:** `{run_data.get('video_path')}`

## Research Sources
"""
        for src in run_data.get("sources", []):
            md_content += f"- [{src.get('title')}]({src.get('url')}) (Relevance Score: {src.get('score', 0):.2f})\n"

        md_content += "\n## Scene Visual Plan\n"
        for sc in run_data.get("scenes", []):
            provider = sc.get("asset_metadata", {}).get("provider", "unknown")
            md_content += f"- **Scene {sc.get('scene_number')}:** `{sc.get('visual_concept')}` | Provider: `{provider}`\n"

        report_file.write_text(md_content, encoding="utf-8")
        logger.info(f"Saved Metadata JSON: {meta_file.resolve()}")
        logger.info(f"Saved Report Markdown: {report_file.resolve()}")

        return meta_file, report_file

class Tuple_Path_Path:
    pass
