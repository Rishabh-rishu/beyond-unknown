"""
BEYOND UNKNOWN - Wikimedia Commons Media Client
Searches and retrieves historical monuments, archaeological artifacts, and nature
imagery from Wikimedia Commons API.
Extracts author, license, and attribution requirements.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests

logger = logging.getLogger("beyond_unknown.assets.wikimedia")

class WikimediaClient:
    def __init__(self):
        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.headers = {
            "User-Agent": "BeyondUnknownBot/1.0 (Documentary Automation; contact@beyondunknown.com)"
        }

    def search_and_download(
        self,
        query: str,
        output_dir: Path,
        scene_id: int
    ) -> Optional[Dict]:
        """
        Searches Wikimedia Commons for relevant CC/Public Domain imagery.
        Downloads the best high-res image and returns license metadata.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        # Clean query for search
        clean_query = query.replace("4k", "").replace("cinematic", "").replace("footage", "").strip()
        logger.info(f"Wikimedia Commons search for scene {scene_id}: '{clean_query}'")

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"file:{clean_query}",
            "gsrnamespace": 6,  # File namespace
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": 1080
        }

        try:
            res = requests.get(self.api_url, params=params, headers=self.headers, timeout=12)
            if res.status_code != 200:
                return None

            data = res.json()
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None

            for page_id, page in pages.items():
                imageinfo_list = page.get("imageinfo", [])
                if not imageinfo_list:
                    continue

                info = imageinfo_list[0]
                img_url = info.get("thumburl") or info.get("url")
                if not img_url:
                    continue

                # Ignore non-image formats (.ogg, .pdf, .svg)
                if not any(img_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                    continue

                # Extract metadata
                meta = info.get("extmetadata", {})
                artist = meta.get("Artist", {}).get("value", "Wikimedia Contributor")
                license_name = meta.get("LicenseShortName", {}).get("value", "Creative Commons / Public Domain")
                desc_url = info.get("descriptionurl", "")

                # Download image
                ext = ".jpg" if ".jpg" in img_url.lower() or ".jpeg" in img_url.lower() else ".png"
                out_path = output_dir / f"scene_{scene_id:02d}_wiki{ext}"
                dl = requests.get(img_url, headers=self.headers, timeout=15)
                if dl.status_code == 200 and len(dl.content) > 5000:
                    with open(out_path, "wb") as f:
                        f.write(dl.content)

                    logger.info(f"Wikimedia image saved for scene {scene_id}: {out_path.name} (License: {license_name})")
                    return {
                        "scene_id": scene_id,
                        "file_path": str(out_path),
                        "media_type": "image",
                        "creator": artist[:60],
                        "source_url": desc_url or img_url,
                        "license": f"Wikimedia Commons ({license_name})"
                    }

        except Exception as e:
            logger.warning(f"Wikimedia search failed for '{query}': {e}")

        return None
