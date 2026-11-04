"""
BEYOND UNKNOWN - Background Music Selector
Selects topic-appropriate licensed ambient tracks, applies audio ducking parameters,
and tracks music licensing and attribution metadata.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from config import settings

logger = logging.getLogger("beyond_unknown.video.music")

class MusicSelector:
    def __init__(self):
        self.audio_dir = settings.AUDIO_DIR
        self.config = settings.get_music_config()
        self.tracks = self.config.get("tracks", {})
        self.settings = self.config.get("settings", {})

    def select_track_for_topic(
        self,
        category: str,
        recent_tracks: Optional[List[str]] = None
    ) -> Dict:
        """
        Selects the best matching music track for the topic category.
        Ensures consecutive videos use varied tracks when possible.
        """
        cat_lower = category.lower()
        candidate_keys = []

        # Find matching tracks by category
        for track_key, track_info in self.tracks.items():
            track_cats = [c.lower() for c in track_info.get("categories", [])]
            if any(cat in cat_lower or cat_lower in cat for cat in track_cats):
                candidate_keys.append(track_key)

        if not candidate_keys:
            candidate_keys = list(self.tracks.keys())

        # Filter out the immediately preceding track if multiple choices exist
        last_track = recent_tracks[-1] if recent_tracks else None
        filtered = [k for k in candidate_keys if k != last_track]
        chosen_key = filtered[0] if filtered else candidate_keys[0]

        chosen_info = self.tracks.get(chosen_key, {})
        filename = chosen_info.get("filename", f"{chosen_key}.mp3")
        file_path = self.audio_dir / filename

        logger.info(f"Selected music track '{chosen_key}' ({chosen_info.get('genre')}) for category '{category}'")

        return {
            "track_key": chosen_key,
            "filename": filename,
            "file_path": str(file_path),
            "ducking_volume": self.settings.get("ducking_volume", 0.12),
            "fade_in_seconds": self.settings.get("fade_in_seconds", 1.5),
            "fade_out_seconds": self.settings.get("fade_out_seconds", 2.0),
            "license": chosen_info.get("license", "Creative Commons CC0"),
            "attribution": chosen_info.get("attribution", "Beyond Unknown Original Ambient Score")
        }
