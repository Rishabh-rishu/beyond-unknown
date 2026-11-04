"""
BEYOND UNKNOWN - Pexels Media Client
Retrieves vertical cinematic video footage and high-res photos from Pexels API.
Tracks creator, original URL, and Pexels license metadata.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from config import settings

logger = logging.getLogger("beyond_unknown.assets.pexels")

class PexelsClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.PEXELS_API_KEY
        self.base_video_url = "https://api.pexels.com/videos/search"
        self.base_photo_url = "https://api.pexels.com/v1/search"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": self.api_key})

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def search_and_download(
        self,
        query: str,
        output_dir: Path,
        scene_id: int,
        prefer_video: bool = True
    ) -> Optional[Dict]:
        """
        Searches Pexels for vertical video or high-res photos.
        Downloads the asset and returns metadata dictionary.
        """
        if not self.is_available():
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Pexels query for scene {scene_id}: '{query}'")

        try:
            # 1. Search vertical video first
            if prefer_video:
                params = {
                    "query": query,
                    "orientation": "portrait",
                    "per_page": 5,
                    "size": "medium"
                }
                res = self.session.get(self.base_video_url, params=params, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    videos = data.get("videos", [])
                    if videos:
                        vid = videos[0]
                        # Select 1080x1920 or highest vertical HD file
                        video_files = vid.get("video_files", [])
                        best_file = None
                        for vf in video_files:
                            w = vf.get("width", 0)
                            h = vf.get("height", 0)
                            if h > w and (w >= 720 or h >= 1280):
                                best_file = vf
                                break
                        if not best_file and video_files:
                            best_file = video_files[0]

                        if best_file and best_file.get("link"):
                            out_path = output_dir / f"scene_{scene_id:02d}_pexels.mp4"
                            dl = self.session.get(best_file["link"], timeout=20, stream=True)
                            if dl.status_code == 200:
                                with open(out_path, "wb") as f:
                                    for chunk in dl.iter_content(chunk_size=1024*64):
                                        f.write(chunk)
                                return {
                                    "scene_id": scene_id,
                                    "file_path": str(out_path),
                                    "media_type": "video",
                                    "creator": vid.get("user", {}).get("name", "Pexels Creator"),
                                    "source_url": vid.get("url", ""),
                                    "license": "Pexels Free-to-use License"
                                }

            # 2. Search high-res photo if no vertical video found
            photo_params = {
                "query": query,
                "orientation": "portrait",
                "per_page": 5
            }
            res_photo = self.session.get(self.base_photo_url, params=photo_params, timeout=12)
            if res_photo.status_code == 200:
                data = res_photo.json()
                photos = data.get("photos", [])
                if photos:
                    photo = photos[0]
                    img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                    if img_url:
                        out_path = output_dir / f"scene_{scene_id:02d}_pexels.jpg"
                        dl = self.session.get(img_url, timeout=15)
                        if dl.status_code == 200:
                            with open(out_path, "wb") as f:
                                f.write(dl.content)
                            return {
                                "scene_id": scene_id,
                                "file_path": str(out_path),
                                "media_type": "image",
                                "creator": photo.get("photographer", "Pexels Photographer"),
                                "source_url": photo.get("url", ""),
                                "license": "Pexels Free-to-use License"
                            }

        except Exception as e:
            logger.warning(f"Pexels search failed for '{query}': {e}")

        return None
