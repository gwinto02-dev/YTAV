from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import TEMP_DIR
from src.media.visual_planner import VisualPlanner
from src.media.visual_provider import ProviderHealthManager
from src.media.pexels_client import PexelsClient
from src.media.pixabay_client import PixabayClient
from src.media.wikimedia_client import WikimediaClient
from src.media.fallback_assets import FallbackAssetsManager
from src.media.asset_validator import AssetValidator
from src.utils.logger import logger

class MediaManager:
    """Orchestrates scene visual sourcing across resilient provider fallback chain."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.planner = VisualPlanner()
        self.health_manager = ProviderHealthManager(failure_threshold=2)
        
        self.pexels = PexelsClient(self.health_manager)
        self.pixabay = PixabayClient(self.health_manager)
        self.wikimedia = WikimediaClient(self.health_manager)
        self.fallback = FallbackAssetsManager()
        self.validator = AssetValidator()

    def source_scene_visuals(self, script_text_or_scenes: Any, topic_name: str = "") -> List[Dict[str, Any]]:
        """
        Source valid visual assets for each scene using fallback chain.
        Accepts either script_text (and plans scenes) or pre-calculated timeline scenes list.
        """
        if isinstance(script_text_or_scenes, list):
            scenes = script_text_or_scenes
        else:
            scenes = self.planner.plan_visuals(script_text_or_scenes, topic_name)

        sourced_scenes = []
        logger.info(f"[MediaManager] Sourcing visuals for {len(scenes)} scenes...")

        for scene in scenes:
            scene_num = scene["scene_number"]
            query = scene["visual_concept"]
            out_file = self.temp_dir / f"scene_{scene_num}_visual.png"

            asset_meta = None

            # Fallback chain: Pexels -> Pixabay -> Wikimedia -> Local Fallback
            providers = [
                ("pexels", self.pexels),
                ("pixabay", self.pixabay),
                ("wikimedia", self.wikimedia)
            ]

            for name, provider in providers:
                if provider.is_available:
                    res = provider.search_and_download(query, out_file)
                    if res:
                        is_valid, reason, _ = self.validator.validate_asset(out_file)
                        if is_valid:
                            logger.info(f" -> Scene {scene_num}: {name.upper()} asset selected ({query})")
                            asset_meta = res
                            break
                        else:
                            logger.warning(f" -> Scene {scene_num}: {name.upper()} asset invalid ({reason})")

            # Use local fallback if no external provider succeeded
            if not asset_meta:
                asset_meta = self.fallback.get_fallback_asset(scene_num, query, out_file)

            scene_record = dict(scene)
            scene_record["asset_path"] = str(out_file)
            scene_record["asset_metadata"] = asset_meta
            sourced_scenes.append(scene_record)

        return sourced_scenes
