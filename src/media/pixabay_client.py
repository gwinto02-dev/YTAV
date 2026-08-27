import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import PIXABAY_API_KEY
from src.media.visual_provider import VisualProvider, ProviderHealthManager
from src.utils.logger import logger

class PixabayClient(VisualProvider):
    """Pixabay API Visual Provider."""

    def __init__(self, health_manager: ProviderHealthManager):
        super().__init__("pixabay", health_manager)
        self.api_key = PIXABAY_API_KEY

    def search_and_download(self, query: str, output_path: Path) -> Optional[Dict[str, Any]]:
        if not self.api_key or not self.is_available:
            return None

        url = f"https://pixabay.com/api/?key={self.api_key}&q={requests.utils.quote(query)}&image_type=photo&orientation=vertical&per_page=3"

        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", [])
                if hits:
                    img_url = hits[0]["largeImageURL"]
                    img_resp = requests.get(img_url, timeout=10)
                    if img_resp.status_code == 200:
                        output_path.write_bytes(img_resp.content)
                        self.health_manager.record_success(self.name)
                        return {
                            "provider": "pixabay",
                            "file_path": str(output_path),
                            "source_url": hits[0].get("pageURL", img_url),
                            "author": hits[0].get("user", "Pixabay"),
                            "license": "Pixabay License"
                        }
            self.health_manager.record_failure(self.name, f"HTTP {resp.status_code} or no hits")
            return None
        except Exception as e:
            self.health_manager.record_failure(self.name, str(e))
            return None
