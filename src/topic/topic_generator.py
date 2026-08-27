import random
from typing import List, Dict, Any
from config.settings import GEMINI_API_KEY
from src.utils.logger import logger

CATEGORIES = [
    "Nature & Earth",
    "Space",
    "Animals",
    "Human Body & Brain",
    "Science",
    "Geography",
    "Unsolved Mysteries"
]

PHENOMENA = {
    "Nature & Earth": [
        "Bioluminescent Ocean Waves", "Volcanic Lightning", "Supercell Thunderstorms",
        "Sailing Stones of Death Valley", "Perpetual Lightning of Catatumbo",
        "Underwater Sinkholes", "Methane Bubbles under Ice", "Blood Falls of Antarctica",
        "Brinicle Ice Fingers of Death", "Fire Rainbows", "Lenticular Clouds",
        "Red Tides of Algae", "Singing Sand Dunes", "Basalt Hexagonal Columns"
    ],
    "Space": [
        "Rogue Planets Floating in Darkness", "Supermassive Black Holes",
        "Neutron Star Crust Hardness", "Magnetar Magnetic Bursts",
        "Gamma Ray Bursts", "Titan Liquid Methane Lakes", "Europa Subsurface Ocean",
        "The Great Attractor", "Dark Matter Halo Anomalies", "Oumuamua Interstellar Object",
        "Solar Flare Coronal Mass Ejections", "Venus Acid Rain Clouds",
        "Enceladus Water Geysers", "Fast Radio Bursts"
    ],
    "Animals": [
        "Tardigrade Extreme Freeze Survival", "Immortal Jellyfish Cellular Reversion",
        "Pistol Shrimp Shockwave Attack", "Electric Eel High Voltage Bursts",
        "Mantids Hyper-speed Strike", "Wood Frog Solid Freeze Hibernation",
        "Cuttlefish Dynamic Camouflage", "Arctic Tern Migration Distance",
        "Honey Badger Immunity to Venom", "Crow Complex Tool Manufacture",
        "Octopus Multi-Brain Autonomy", "Axolotl Complete Limb Regeneration"
    ],
    "Human Body & Brain": [
        "Lucid Dreaming Neurological State", "Phantasm Memory Creation",
        "Phantom Limb Syndrome Signals", "Synesthesia Cross-Sensory Wiring",
        "Hyperthymesia Absolute Memory", "REM Sleep Motor Paralysis",
        "Neuroplasticity Brain Rewiring", "Placebo Effect Endorphin Release",
        "Capgras Delusion Impostor Belief", "Deja Vu Neural Delay",
        "Stendhal Syndrome Sensory Overload"
    ],
    "Science": [
        "Quantum Entanglement Action", "Double Slit Wave Particle Duality",
        "Aerogel Ultralight Density", "Superfluid Liquid Helium Zero Friction",
        "Antimatter Annihilation Energy", "Graphene Molecular Strength",
        "Bose-Einstein Condensate Zero Temp", "Time Dilation at High Speeds",
        "Sonoluminescence Light from Sound", "Cherenkov Radiation Blue Glow"
    ],
    "Geography": [
        "Door to Hell Darvaza Crater", "Bermuda Triangle Magnetic Anomaly",
        "Point Nemo Isolated Ocean Pole", "Kawa Ijen Blue Lava Volcano",
        "Lake Natron Calcifying Waters", "Eye of the Sahara Richat Structure",
        "Mount Roraima Tepui Plateaus", "Movile Cave Isolated Ecosystem",
        "Lake Baikal Deep Freshwater Ice", "Socotra Island Dragon Blood Trees"
    ],
    "Unsolved Mysteries": [
        "The Wow Signal Deep Space Beacon", "Voynich Manuscript Cipher",
        "Taos Hum Low Frequency Resonance", "Oak Island Money Pit Structure",
        "The Baltic Sea Anomaly Object", "Dyatlov Pass Anomalous Event",
        "Hessdalen Lights Plasma Orbs", "Marfa Mystery Lights",
        "Kryptos Sculpture Unsolved Section", "Bloop Deep Ocean Sound"
    ]
}

TEMPLATES = [
    "Why Does {phenomenon} Happen?",
    "The Strange Science Behind {phenomenon}",
    "Scientists Still Cannot Fully Explain {phenomenon}",
    "What Really Happens During {phenomenon}?",
    "The Bizarre Mystery of {phenomenon}",
    "How {phenomenon} Defies Known Science",
    "Unlocking the Secret of {phenomenon}",
    "Inside the Mind-Blowing Phenomenon of {phenomenon}",
    "Why {phenomenon} Confounds Researchers",
    "The Terrifying Reality of {phenomenon}"
]

class TopicGenerator:
    """Dynamic generator producing candidate topics without polluting database history."""
    
    def generate_candidates(self, count: int = 60, seed_offset: int = 0) -> List[Dict[str, str]]:
        """Generate a fresh list of candidate topics with category metadata."""
        candidates = []
        rng = random.Random(seed_offset if seed_offset > 0 else None)
        
        # Build deterministic combinatorial pool
        all_combinations = []
        for cat, items in PHENOMENA.items():
            for item in items:
                for tmpl in TEMPLATES:
                    topic_text = tmpl.format(phenomenon=item)
                    all_combinations.append({"topic_name": topic_text, "category": cat})
        
        # Shuffle with RNG seed offset for variety
        rng.shuffle(all_combinations)
        
        # Select requested count
        candidates = all_combinations[:count]
        
        # Try LLM generation if configured and API key available
        if GEMINI_API_KEY:
            llm_candidates = self._try_llm_generation(count=10)
            if llm_candidates:
                candidates = llm_candidates + candidates
                
        return candidates

    def _try_llm_generation(self, count: int = 10) -> List[Dict[str, str]]:
        """Optional LLM candidate generation using google-genai SDK if configured."""
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"Generate {count} unique factual topic ideas for short YouTube mystery/educational videos. "
                f"Categories: {', '.join(CATEGORIES)}. "
                f"Format each line as: Category | Topic Title"
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            results = []
            if response and response.text:
                for line in response.text.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|", 1)
                        cat = parts[0].strip()
                        top = parts[1].strip()
                        if cat in CATEGORIES and len(top) > 10:
                            results.append({"topic_name": top, "category": cat})
            return results
        except Exception as e:
            logger.debug(f"LLM topic candidate generation skipped/failed: {e}")
            return []
