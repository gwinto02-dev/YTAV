import random
from typing import Dict, Any, List
from config.settings import GEMINI_API_KEY, MIN_WORD_COUNT, MAX_WORD_COUNT
from src.utils.logger import logger
from src.utils.text_utils import extract_meaningful_tokens

HOOK_TEMPLATES = [
    "Imagine discovering a phenomenon so strange that scientists still struggle to explain it.",
    "Did you know that out in the natural world, something completely mind-blowing occurs under our very noses?",
    "What if everything you thought you knew about nature was challenged by one unbelievable discovery?",
    "Deep within our universe lies a mystery so strange it almost sounds like science fiction.",
    "Scientists recently uncovered a secret that changes the way we understand our world."
]

ENDING_TEMPLATES = [
    "And the most surprising part? Researchers believe we have only scratched the surface of what is truly happening.",
    "Which makes you wonder: what other incredible mysteries are waiting to be uncovered right beside us?",
    "And as technology advances, this incredible phenomenon continues to challenge our understanding of reality.",
    "The world is filled with unbelievable secrets, and this is just one of many waiting to be understood."
]

class ScriptGenerator:
    """Generates original grounded Short scripts (90-150 words) and candidate titles."""

    def generate_script_and_titles(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured script, word count, hook, and 3-5 candidate titles from research data.
        """
        topic_name = research_data["topic"]
        category = research_data.get("category", "Science")
        facts = research_data.get("facts", [])

        logger.info(f"Generating script for topic: '{topic_name}'...")

        # Try LLM if configured
        if GEMINI_API_KEY:
            llm_result = self._try_llm_script(topic_name, category, facts)
            if llm_result:
                return llm_result

        # Grounded deterministic synthesis
        return self._synthesize_script(topic_name, category, facts)

    def _synthesize_script(self, topic_name: str, category: str, facts: List[str]) -> Dict[str, Any]:
        """Synthesize a structured script using research facts."""
        hook = random.choice(HOOK_TEMPLATES)
        ending = random.choice(ENDING_TEMPLATES)
        
        # Build context and main facts
        fact_text_1 = facts[0] if len(facts) > 0 else f"{topic_name} represents an extraordinary biological and environmental anomaly."
        fact_text_2 = facts[1] if len(facts) > 1 else "Observational data demonstrates unique environmental interactions across varying conditions."
        fact_text_3 = facts[2] if len(facts) > 2 else "Laboratory analyses continue to measure these astonishing natural effects under controlled testing."

        context = f"When researchers first began studying {topic_name.lower()}, they immediately noticed something remarkable. {fact_text_1}"
        main_fact = f"What makes this particularly fascinating is the underlying scientific mechanism. {fact_text_2}"
        explanation = f"According to detailed scientific analysis, {fact_text_3} This phenomenon highlights how complex natural systems operate."
        padding = "Every new measurement raises intriguing questions among experts studying these fundamental laws of nature."

        full_script = f"{hook} {context} {main_fact} {explanation} {padding} {ending}"
        
        # Adjust if needed
        words = full_script.split()
        if len(words) > MAX_WORD_COUNT:
            full_script = f"{hook} {context} {main_fact} {explanation} {ending}"

        candidate_titles = self.generate_titles(topic_name, facts)

        return {
            "topic": topic_name,
            "category": category,
            "hook": hook,
            "script_text": full_script,
            "word_count": len(full_script.split()),
            "candidate_titles": candidate_titles,
            "selected_title": candidate_titles[0]
        }

    def generate_titles(self, topic_name: str, facts: List[str]) -> List[str]:
        """Generate 3-5 specific, non-generic title options."""
        tokens = list(extract_meaningful_tokens(topic_name))
        core_concept = " ".join(tokens[:3]).title() if tokens else "Phenomenon"

        titles = [
            f"The Mind-Blowing Secret of {core_concept}",
            f"Why {core_concept} Defies Science",
            f"The Mystery Behind {core_concept} Explained",
            f"What Makes {core_concept} So Strange?",
            f"Scientists Couldn't Believe {core_concept}"
        ]
        return list(dict.fromkeys(titles))[:5]

    def _try_llm_script(self, topic_name: str, category: str, facts: List[str]) -> Any:
        """Optional LLM script generation using google-genai SDK."""
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            facts_str = "\n".join([f"- {f}" for f in facts])
            prompt = (
                f"Write an exciting, grounded 100-130 word YouTube Short script about: {topic_name}.\n"
                f"Grounded Facts to include:\n{facts_str}\n\n"
                f"Format requirement:\n"
                f"HOOK: ...\n"
                f"SCRIPT: ...\n"
                f"TITLES:\n1. ...\n2. ...\n3. ..."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response and response.text:
                text = response.text
                if "SCRIPT:" in text and "TITLES:" in text:
                    parts = text.split("SCRIPT:")[1].split("TITLES:")
                    script_body = parts[0].strip()
                    title_lines = [l.strip().lstrip("0123456789.- ") for l in parts[1].strip().split("\n") if len(l.strip()) > 5]
                    
                    word_cnt = len(script_body.split())
                    if MIN_WORD_COUNT <= word_cnt <= MAX_WORD_COUNT and len(title_lines) >= 3:
                        return {
                            "topic": topic_name,
                            "category": category,
                            "hook": script_body.split(".")[0] + ".",
                            "script_text": script_body,
                            "word_count": word_cnt,
                            "candidate_titles": title_lines[:5],
                            "selected_title": title_lines[0]
                        }
            return None
        except Exception as e:
            logger.debug(f"LLM script generation skipped/failed: {e}")
            return None
