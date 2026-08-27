import random
from pathlib import Path
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFilter
from config.settings import FALLBACK_IMAGES_DIR, VIDEO_WIDTH, VIDEO_HEIGHT
from src.utils.logger import logger

THEME_COLORS = {
    "space": [(10, 15, 35), (25, 45, 85), (5, 5, 20)],
    "ocean": [(5, 35, 60), (10, 75, 120), (2, 20, 40)],
    "nature": [(15, 45, 25), (35, 85, 45), (10, 30, 15)],
    "science": [(20, 20, 50), (60, 40, 110), (15, 10, 35)],
    "mystery": [(40, 15, 45), (85, 30, 75), (20, 5, 25)],
    "abstract": [(30, 30, 30), (70, 70, 70), (15, 15, 15)]
}

class FallbackAssetsManager:
    """Generates procedural high-resolution 1080x1920 visual backdrops when external providers fail."""

    def __init__(self, fallback_dir: Path = FALLBACK_IMAGES_DIR):
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

    def get_fallback_asset(self, scene_number: int, query: str, output_path: Path) -> Dict[str, Any]:
        """
        Generate or fetch a high-res 1080x1920 themed fallback visual.
        """
        query_lower = query.lower()
        theme = "abstract"
        if any(w in query_lower for w in ["space", "star", "black hole", "planet", "galaxy", "cosmic"]):
            theme = "space"
        elif any(w in query_lower for w in ["ocean", "wave", "water", "sea", "underwater", "ice"]):
            theme = "ocean"
        elif any(w in query_lower for w in ["tree", "forest", "animal", "frog", "nature", "earth"]):
            theme = "nature"
        elif any(w in query_lower for w in ["science", "lab", "brain", "quantum", "physics"]):
            theme = "science"
        elif any(w in query_lower for w in ["mystery", "unsolved", "signal", "light"]):
            theme = "mystery"

        bg_file = self.fallback_dir / f"fallback_{theme}_{scene_number}.png"
        if not bg_file.exists():
            self._create_procedural_backdrop(bg_file, theme)

        # Copy/save to output_path
        img = Image.open(bg_file)
        img.save(output_path)
        
        logger.info(f"Local Fallback visual asset selected for Scene {scene_number} (Theme: {theme})")
        return {
            "provider": "local_fallback",
            "file_path": str(output_path),
            "source_url": "local_procedural_asset",
            "author": "System Fallback Generator",
            "license": "Internal Project Asset"
        }

    def _create_procedural_backdrop(self, target_path: Path, theme: str):
        """Create procedural vertical 1080x1920 gradient with atmospheric particle effects."""
        cols = THEME_COLORS.get(theme, THEME_COLORS["abstract"])
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), cols[0])
        draw = ImageDraw.Draw(img)

        # Vertical gradient
        for y in range(VIDEO_HEIGHT):
            ratio = y / float(VIDEO_HEIGHT)
            r = int(cols[0][0] * (1 - ratio) + cols[1][0] * ratio)
            g = int(cols[0][1] * (1 - ratio) + cols[1][1] * ratio)
            b = int(cols[0][2] * (1 - ratio) + cols[1][2] * ratio)
            draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))

        # Add atmospheric geometric particles / glow spots
        rng = random.Random(hash(theme) + y)
        for _ in range(30):
            cx = rng.randint(50, VIDEO_WIDTH - 50)
            cy = rng.randint(50, VIDEO_HEIGHT - 50)
            radius = rng.randint(40, 300)
            color = cols[2] if rng.random() > 0.5 else cols[1]
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

        img = img.filter(ImageFilter.GaussianBlur(radius=30))
        img.save(target_path)
