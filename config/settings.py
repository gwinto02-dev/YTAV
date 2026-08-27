import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if available
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database configuration
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "history.sqlite"))

# Output directories
OUTPUT_DIR = BASE_DIR / "output"
VIDEOS_DIR = OUTPUT_DIR / "videos"
REPORTS_DIR = OUTPUT_DIR / "reports"
METADATA_DIR = OUTPUT_DIR / "metadata"
TEMP_DIR = BASE_DIR / "temp"

# Assets directories
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FALLBACK_IMAGES_DIR = ASSETS_DIR / "fallback_images"
FONTS_DIR = ASSETS_DIR / "fonts"

# API Keys
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Pipeline configuration
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
VOICE_NAME = os.getenv("VOICE_NAME", "en-US-ChristopherNeural")
COOLDOWN_DAYS = int(os.getenv("COOLDOWN_DAYS", "14"))

# Video specifications
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
TARGET_FPS = 30
MIN_DURATION_SECS = 35
MAX_DURATION_SECS = 60
MIN_WORD_COUNT = 90
MAX_WORD_COUNT = 150

# Subtitle / Karaoke Caption configuration
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", "24"))
CAPTION_FONT_FAMILY = os.getenv("CAPTION_FONT_FAMILY", "Arial")
CAPTION_PRIMARY_COLOR = os.getenv("CAPTION_PRIMARY_COLOR", "&H00FFFFFF")  # White
CAPTION_HIGHLIGHT_COLOR = os.getenv("CAPTION_HIGHLIGHT_COLOR", "&H0000FFFF")  # Vibrant Yellow/Cyan
CAPTION_OUTLINE_COLOR = os.getenv("CAPTION_OUTLINE_COLOR", "&H00000000")  # Black
CAPTION_OUTLINE_THICKNESS = int(os.getenv("CAPTION_OUTLINE_THICKNESS", "3"))
CAPTION_SHADOW = int(os.getenv("CAPTION_SHADOW", "1"))
CAPTION_WORDS_PER_GROUP = int(os.getenv("CAPTION_WORDS_PER_GROUP", "5"))
CAPTION_VERTICAL_POSITION = int(os.getenv("CAPTION_VERTICAL_POSITION", "220"))

def ensure_directories():
    """Ensure all required project directories exist."""
    dirs = [
        BASE_DIR / "data",
        VIDEOS_DIR,
        REPORTS_DIR,
        METADATA_DIR,
        TEMP_DIR,
        MUSIC_DIR,
        FALLBACK_IMAGES_DIR,
        FONTS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Run directory check on import
ensure_directories()
