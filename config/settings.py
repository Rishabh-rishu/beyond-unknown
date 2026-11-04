"""
BEYOND UNKNOWN - Global Settings and Environment Configuration
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Base Project Paths
CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_DIR = PROJECT_ROOT / "output"
VIDEOS_OUTPUT_DIR = OUTPUT_DIR / "videos"
AUDIO_OUTPUT_DIR = OUTPUT_DIR / "audio"
SCRIPTS_OUTPUT_DIR = OUTPUT_DIR / "scripts"
METADATA_OUTPUT_DIR = OUTPUT_DIR / "metadata"

# Load local environment
load_dotenv(PROJECT_ROOT / ".env")

# 1. AI Engine - Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash").strip()

# 2. Visual Acquisition
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()

# 3. YouTube API & OAuth
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()

# 4. Voiceover & Audio
VOICE_NAME = os.getenv("VOICE_NAME", "hi-IN-MadhurNeural").strip()
VOICE_RATE = os.getenv("VOICE_RATE", "+15%").strip()
AUDIO_TEMPO = float(os.getenv("AUDIO_TEMPO", "1.15"))

# 5. Scheduling
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata").strip()
MORNING_PUBLISH_TIME = os.getenv("MORNING_PUBLISH_TIME", "09:30").strip()
EVENING_PUBLISH_TIME = os.getenv("EVENING_PUBLISH_TIME", "17:30").strip()
SCHEDULING_BUFFER_MINUTES = int(os.getenv("SCHEDULING_BUFFER_MINUTES", "45"))

# Brand configuration loader
def get_brand_config() -> Dict[str, Any]:
    brand_file = CONFIG_DIR / "brand.json"
    if brand_file.exists():
        with open(brand_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Music configuration loader
def get_music_config() -> Dict[str, Any]:
    music_file = CONFIG_DIR / "music_config.json"
    if music_file.exists():
        with open(music_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Font path resolver with fallback
def get_font_path(font_type: str = "heading") -> Optional[Path]:
    brand = get_brand_config()
    relative_path = brand.get("typography", {}).get("font_paths", {}).get(font_type)
    if relative_path:
        full_path = PROJECT_ROOT / relative_path
        if full_path.exists():
            return full_path
    
    # Check directory for any matching ttf
    for file in FONTS_DIR.glob("*.ttf"):
        if font_type.lower() in file.stem.lower():
            return file
    
    # Generic fallback to any font in directory
    all_fonts = list(FONTS_DIR.glob("*.ttf"))
    return all_fonts[0] if all_fonts else None
