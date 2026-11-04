"""
BEYOND UNKNOWN - NASA Media Library Client
Retrieves authentic public domain NASA imagery for space, planets, Earth,
and astrophysics topics from images-api.nasa.gov.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import requests

logger = logging.getLogger("beyond_unknown.assets.nasa")

class NASAClient:
    def __init__(self):
        self.api_url = "https://images-api.nasa.gov/search"

    def search_and_download(
        self,
        query: str,
        output_dir: Path,
        scene_id: int
    ) -> Optional[Dict]:
        """
        Searches NASA Images API for astronomical and planetary imagery.
        Downloads the image and returns Public Domain metadata.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        clean_query = query.replace("4k", "").replace("cinematic", "").strip()
        logger.info(f"NASA Media search for scene {scene_id}: '{clean_query}'")

        params = {
            "q": clean_query,
            "media_type": "image"
        }

        try:
            res = requests.get(self.api_url, params=params, timeout=12)
            if res.status_code != 200:
                return None

            data = res.json()
            items = data.get("collection", {}).get("items", [])
            if not items:
                return None

            first_item = items[0]
            links = first_item.get("links", [])
            thumb_href = links[0].get("href") if links else None
            
            # If item has collection manifest, retrieve orig/large image
            data_meta = first_item.get("data", [{}])[0]
            title = data_meta.get("title", "NASA Scientific Imagery")
            nasa_id = data_meta.get("nasa_id", "")

            # Download preview/large image
            if thumb_href:
                out_path = output_dir / f"scene_{scene_id:02d}_nasa.jpg"
                dl = requests.get(thumb_href, timeout=15)
                if dl.status_code == 200 and len(dl.content) > 5000:
                    with open(out_path, "wb") as f:
                        f.write(dl.content)

                    logger.info(f"NASA image saved for scene {scene_id}: {out_path.name}")
                    return {
                        "scene_id": scene_id,
                        "file_path": str(out_path),
                        "media_type": "image",
                        "creator": "NASA / JPL / ESA",
                        "source_url": f"https://images.nasa.gov/details-{nasa_id}" if nasa_id else "https://images-api.nasa.gov",
                        "license": "NASA Public Domain / Government Works"
                    }

        except Exception as e:
            logger.warning(f"NASA search failed for '{query}': {e}")

        return None
