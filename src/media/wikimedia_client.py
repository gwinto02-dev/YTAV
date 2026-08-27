import requests
from pathlib import Path
from typing import Optional, Dict, Any
from src.media.visual_provider import VisualProvider, ProviderHealthManager
from src.utils.logger import logger

WIKIMEDIA_COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AmazingFactsAutomationBot/1.0 (educational_automation_project)"

class WikimediaClient(VisualProvider):
    """Wikimedia Commons API Visual Provider."""

    def __init__(self, health_manager: ProviderHealthManager):
        super().__init__("wikimedia", health_manager)

    def search_and_download(self, query: str, output_path: Path) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            return None

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"file:{query}",
            "gsrnamespace": 6,
            "gsrlimit": 3,
            "prop": "imageinfo",
            "iiprop": "url|mime|user|extmetadata",
            "format": "json"
        }
        headers = {"User-Agent": USER_AGENT}

        try:
            resp = requests.get(WIKIMEDIA_COMMONS_API, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for pid, pinfo in pages.items():
                    imageinfo = pinfo.get("imageinfo", [])
                    if imageinfo:
                        img_url = imageinfo[0].get("url")
                        mime = imageinfo[0].get("mime", "")
                        if img_url and ("image/jpeg" in mime or "image/png" in mime or "image/webp" in mime):
                            img_resp = requests.get(img_url, headers=headers, timeout=10)
                            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                output_path.write_bytes(img_resp.content)
                                self.health_manager.record_success(self.name)
                                return {
                                    "provider": "wikimedia",
                                    "file_path": str(output_path),
                                    "source_url": img_url,
                                    "author": imageinfo[0].get("user", "Wikimedia Commons"),
                                    "license": "Wikimedia Commons CC/Public Domain"
                                }
            self.health_manager.record_failure(self.name, f"HTTP {resp.status_code} or no valid image files")
            return None
        except Exception as e:
            self.health_manager.record_failure(self.name, f"Network error: {e}")
            return None
