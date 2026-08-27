import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import PEXELS_API_KEY
from src.media.visual_provider import VisualProvider, ProviderHealthManager
from src.utils.logger import logger

class PexelsClient(VisualProvider):
    """Pexels API Visual Provider."""

    def __init__(self, health_manager: ProviderHealthManager):
        super().__init__("pexels", health_manager)
        self.api_key = PEXELS_API_KEY

    def search_and_download(self, query: str, output_path: Path) -> Optional[Dict[str, Any]]:
        if not self.api_key or not self.is_available:
            return None

        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=3&orientation=portrait"
        headers = {"Authorization": self.api_key}

        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                photos = data.get("photos", [])
                if photos:
                    img_url = photos[0]["src"]["large"]
                    img_resp = requests.get(img_url, timeout=10)
                    if img_resp.status_code == 200:
                        output_path.write_bytes(img_resp.content)
                        self.health_manager.record_success(self.name)
                        return {
                            "provider": "pexels",
                            "file_path": str(output_path),
                            "source_url": photos[0].get("url", img_url),
                            "author": photos[0].get("photographer", "Pexels"),
                            "license": "Pexels License"
                        }
            self.health_manager.record_failure(self.name, f"HTTP {resp.status_code} or no photos")
            return None
        except Exception as e:
            self.health_manager.record_failure(self.name, str(e))
            return None
