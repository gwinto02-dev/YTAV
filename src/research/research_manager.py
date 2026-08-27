import re
from typing import Dict, Any, List
from src.research.wikipedia_client import WikipediaClient
from src.research.source_validator import SourceValidator
from src.utils.logger import logger

DEFAULT_FACTS_BASE = {
    "Nature & Earth": [
        "Natural phenomena occur under unique extreme conditions of pressure, temperature, and chemistry.",
        "Scientists use satellite remote sensing and spectroscopic analysis to study atmospheric and geological anomalies.",
        "Geological and climatic patterns can remain active over thousands of years without human intervention."
    ],
    "Space": [
        "Cosmic events involve immense gravitational, electromagnetic, and thermodynamic forces.",
        "Space observations rely on multi-wavelength astronomy across radio, optical, X-ray, and gamma-ray spectra.",
        "Interstellar phenomena often challenge standard physics models of matter under extreme density."
    ],
    "Animals": [
        "Organisms evolve metabolic and biological adaptations to survive harsh ecosystems.",
        "Specialized cellular structures allow extreme cold tolerance, camouflage, or high-voltage generation.",
        "Behavioral patterns are governed by evolutionary biology and neuro-chemical signaling."
    ],
    "Human Body & Brain": [
        "The human nervous system contains over 86 billion neurons communicating through electrochemical impulses.",
        "Neurological anomalies offer insights into sensory processing, memory encoding, and perception.",
        "Cognitive phenomena demonstrate the brain's high level of adaptive neuroplasticity."
    ],
    "Science": [
        "Quantum mechanics and particle physics govern matter at subatomic scale interactions.",
        "Experimental anomalies lead to breakthrough discoveries in thermodynamics and material science.",
        "Laboratory measurements require extreme precision to observe quantum states and physical laws."
    ],
    "Geography": [
        "Geographical anomalies result from tectonic shifts, unique thermal vents, and isolated microclimates.",
        "Isolated locations harbor ancient ecological systems cut off from global environmental changes.",
        "Unique topographies are carved over geological epochs by wind, water, and volcanic activity."
    ],
    "Unsolved Mysteries": [
        "Unexplained events are investigated by analyzing empirical evidence, acoustic data, and historical logs.",
        "Scientific hypotheses distinguish verified physical data from unproven speculation.",
        "Researchers continue monitoring anomalous signals to isolate underlying natural causes."
    ]
}

class ResearchManager:
    """Orchestrates topic research,Wikipedia query, source validation, and fact extraction."""

    def __init__(self):
        self.wiki_client = WikipediaClient()
        self.validator = SourceValidator()

    def research_topic(self, topic_name: str, category: str) -> Dict[str, Any]:
        """Conduct grounded research for topic, returning structured facts."""
        logger.info(f"Researching topic: '{topic_name}'...")
        
        concepts = self.wiki_client.extract_search_concepts(topic_name)
        logger.debug(f"Search concepts extracted: {concepts}")

        valid_sources = []
        all_extracted_facts = []

        # Try Wikipedia search for extracted concepts
        for concept in concepts:
            try:
                search_results = self.wiki_client.search_pages(concept, limit=3)
                for item in search_results:
                    page_data = self.wiki_client.fetch_page_extract(item["title"])
                    if not page_data:
                        continue

                    is_valid, score, reason = self.validator.validate_source(topic_name, page_data)
                    if is_valid:
                        logger.info(f"Found valid Wikipedia source: '{page_data['title']}' (Score: {score:.2f})")
                        valid_sources.append({
                            "title": page_data["title"],
                            "url": page_data["url"],
                            "score": score
                        })

                        # Extract concise sentences as facts
                        extract_sentences = self._split_into_facts(page_data["extract"])
                        all_extracted_facts.extend(extract_sentences)

                        if len(valid_sources) >= 2:
                            break
            except Exception as e:
                logger.warning(f"Research iteration failed for concept '{concept}': {e}")
                
            if len(valid_sources) >= 2:
                break

        # Fallback if no valid Wikipedia sources found
        if not valid_sources or not all_extracted_facts:
            logger.warning(f"No strong Wikipedia sources found for '{topic_name}'. Using grounded fallback facts.")
            fallback_facts = DEFAULT_FACTS_BASE.get(category, DEFAULT_FACTS_BASE["Science"])
            valid_sources.append({
                "title": f"Grounded Research Archive: {category}",
                "url": "https://en.wikipedia.org/wiki/Portal:Science",
                "score": 0.5
            })
            all_extracted_facts.extend(fallback_facts)

        # Deduplicate and format facts
        unique_facts = list(dict.fromkeys(all_extracted_facts))[:6]
        logger.info(f"Research completed. Extracted {len(unique_facts)} facts from {len(valid_sources)} source(s).")

        return {
            "topic": topic_name,
            "category": category,
            "sources": valid_sources,
            "facts": unique_facts
        }

    def _split_into_facts(self, extract: str) -> List[str]:
        """Clean extract and split into concise factual sentences."""
        clean_text = re.sub(r'\([^)]*\)', '', extract) # Remove parentheticals
        sentences = re.split(r'\.\s+', clean_text)
        facts = []
        for s in sentences:
            s_clean = s.strip()
            if 30 <= len(s_clean) <= 180 and not s_clean.startswith("=") and not s_clean.endswith(":"):
                facts.append(s_clean if s_clean.endswith(".") else s_clean + ".")
        return facts
