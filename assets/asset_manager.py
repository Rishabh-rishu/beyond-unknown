"""
BEYOND UNKNOWN - Visual Asset Manager
Orchestrates multi-provider media acquisition:
Priority 1: Pexels API (if key configured)
Priority 2: NASA Media Library (space/planetary)
Priority 3: Wikimedia Commons (historical, monuments, archaeology)
Priority 4: Procedural Cinematic Documentary Visuals (high-res compositing)
Outputs validated 1080x1920 scene assets with license tracking.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import settings
from ai.script_generator import ShortScriptSchema, SceneItem
from assets.pexels_client import PexelsClient
from assets.wikimedia_client import WikimediaClient
from assets.nasa_client import NASAClient
from assets.procedural_graphics import ProceduralGraphics

logger = logging.getLogger("beyond_unknown.assets.manager")

class AssetManager:
    def __init__(self):
        self.pexels = PexelsClient()
        self.wikimedia = WikimediaClient()
        self.nasa = NASAClient()
        self.procedural = ProceduralGraphics()

    def acquire_scene_assets(
        self,
        script: ShortScriptSchema,
        topic_title: str,
        category: str,
        run_assets_dir: Path
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Retrieves, composites, and validates media assets for each scene in the script.
        Returns:
            scenes_data: list of dicts with final composed 1080x1920 image path and camera motion
            licenses: list of attribution and license metadata records
        """
        run_assets_dir.mkdir(parents=True, exist_ok=True)
        raw_downloads_dir = run_assets_dir / "raw"
        composed_dir = run_assets_dir / "composed"
        raw_downloads_dir.mkdir(exist_ok=True)
        composed_dir.mkdir(exist_ok=True)

        is_space = "space" in category.lower() or "astronomy" in category.lower()
        is_science = "science" in category.lower()

        scenes_data = []
        licenses = []

        logger.info(f"Acquiring visual assets for {len(script.scenes)} scenes...")

        for scene in script.scenes:
            scene_id = scene.scene_id
            query = scene.visual_keywords
            media_info = None

            # 1. Priority 1: Pexels API if configured
            if self.pexels.is_available():
                media_info = self.pexels.search_and_download(
                    query=query,
                    output_dir=raw_downloads_dir,
                    scene_id=scene_id,
                    prefer_video=False  # For static pan/zoom Ken Burns compositing
                )

            # 2. Priority 2: NASA (if space or astrophysics)
            if not media_info and (is_space or is_science):
                media_info = self.nasa.search_and_download(
                    query=query,
                    output_dir=raw_downloads_dir,
                    scene_id=scene_id
                )

            # 3. Priority 3: Wikimedia Commons
            if not media_info:
                media_info = self.wikimedia.search_and_download(
                    query=query,
                    output_dir=raw_downloads_dir,
                    scene_id=scene_id
                )

            # Record licensing if downloaded from external source
            base_media_path = None
            if media_info:
                base_media_path = media_info.get("file_path")
                licenses.append({
                    "scene_id": scene_id,
                    "creator": media_info.get("creator", "Unknown"),
                    "source_url": media_info.get("source_url", ""),
                    "license": media_info.get("license", "Public / CC")
                })
            else:
                licenses.append({
                    "scene_id": scene_id,
                    "creator": "Beyond Unknown Creative Studio",
                    "source_url": "Procedural Documentary Graphic Engine",
                    "license": "Channel Original Artwork"
                })

            # 4. Composite final 1080x1920 scene visual with Fact Card & Branding
            composed_path = composed_dir / f"scene_{scene_id:02d}_final.jpg"
            final_img_path = self.procedural.compose_scene_image(
                base_media_path=base_media_path,
                topic_title=topic_title,
                category=category,
                scene_on_screen_text=scene.on_screen_text,
                highlight_words=scene.highlight_words,
                layout_style=scene.layout_style,
                output_image_path=composed_path
            )

            scenes_data.append({
                "scene_id": scene_id,
                "time_range": scene.time_range,
                "image_path": str(final_img_path),
                "camera_motion": scene.camera_motion,
                "narration_chunk": scene.narration_chunk
            })

        logger.info(f"Asset acquisition and composition completed for all {len(scenes_data)} scenes.")
        return scenes_data, licenses
