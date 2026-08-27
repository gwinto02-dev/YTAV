import requests
from typing import List, Dict, Any, Optional
from src.utils.text_utils import extract_meaningful_tokens, extract_concise_keywords
from src.utils.logger import logger
from src.utils.retry import retry

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "AmazingFactsAutomationBot/1.0 (educational_automation_project)"

class WikipediaClient:
    """Client for querying Wikipedia API with concise search concept extraction."""

    def extract_search_concepts(self, topic_name: str) -> List[str]:
        """Extract concise 2-4 word search concepts from topic name."""
        keywords = extract_concise_keywords(topic_name, max_words=4)
        tokens = list(extract_meaningful_tokens(topic_name))
        
        concepts = [keywords]
        if len(tokens) >= 2:
            concepts.append(" ".join(tokens[:2]))
        if len(tokens) >= 3:
            concepts.append(" ".join(tokens[1:3]))
            
        return list(dict.fromkeys([c for c in concepts if len(c) > 2]))

    def search_pages(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Wikipedia pages for a given concise query."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit
        }
        headers = {"User-Agent": USER_AGENT}
        
        try:
            resp = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=5)
            if resp.status_code != 200:
                logger.warning(f"Wikipedia search returned HTTP status {resp.status_code}")
                return []
            data = resp.json()
            search_results = data.get("query", {}).get("search", [])
            return [
                {
                    "pageid": item["pageid"],
                    "title": item["title"],
                    "snippet": item.get("snippet", "")
                }
                for item in search_results
            ]
        except Exception as e:
            logger.warning(f"Wikipedia search failed for query '{query}': {e}")
            return []

    @retry(max_attempts=2, delay=1.0)
    def fetch_page_extract(self, page_title: str) -> Optional[Dict[str, Any]]:
        """Fetch summary extract for a specific page title."""
        params = {
            "action": "query",
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "inprop": "url",
            "titles": page_title,
            "format": "json"
        }
        headers = {"User-Agent": USER_AGENT}
        
        try:
            resp = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=5)
            if resp.status_code != 200:
                return None
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page_info in pages.items():
                if pid == "-1":
                    continue
                return {
                    "pageid": page_info.get("pageid"),
                    "title": page_info.get("title"),
                    "url": page_info.get("fullurl", f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"),
                    "extract": page_info.get("extract", "")
                }
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch Wikipedia extract for '{page_title}': {e}")
            return None
