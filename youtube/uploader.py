"""
BEYOND UNKNOWN - YouTube Video Uploader
Uploads video as private, schedules publication using publishAt RFC 3339 timestamp,
uploads custom cover thumbnail, and sets documentary metadata.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import settings
from youtube.auth import YouTubeAuth

logger = logging.getLogger("beyond_unknown.youtube.uploader")

class YouTubeUploader:
    def __init__(self):
        self.auth = YouTubeAuth()

    def upload_and_schedule_short(
        self,
        video_path: Path,
        thumbnail_path: Optional[Path],
        title: str,
        description: str,
        tags: List[str],
        publish_at_rfc3339: str,
        dry_run: bool = False
    ) -> Tuple[bool, str, str]:
        """
        Uploads the video file to YouTube Data API v3 and schedules publication.
        Returns: (success: bool, youtube_video_id: str, message: str)
        """
        if dry_run or not self.auth.is_configured():
            mock_id = f"mock_yt_{Path(video_path).stem}"
            logger.info(
                f"[DRY-RUN / UNCONFIGURED] Simulated YouTube upload for '{title}'. "
                f"publishAt: {publish_at_rfc3339}, Mock Video ID: {mock_id}"
            )
            return True, mock_id, "Dry-run upload simulation successful."

        from googleapiclient.http import MediaFileUpload

        service = self.auth.get_authenticated_service()
        if not service:
            return False, "", "Could not establish authenticated YouTube API service."

        logger.info(f"Uploading {video_path.name} to YouTube Data API v3 (Scheduled: {publish_at_rfc3339})...")

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:30],
                "categoryId": "27",  # Education
                "defaultLanguage": "hi",
                "defaultAudioLanguage": "hi"
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": publish_at_rfc3339,
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            # Resumable chunked upload
            media = MediaFileUpload(
                str(video_path),
                mimetype="video/mp4",
                chunksize=1024 * 1024 * 4,
                resumable=True
            )

            insert_request = service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"YouTube upload progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            if not video_id:
                return False, "", "YouTube API did not return a valid video ID."

            logger.info(f"Video uploaded successfully! Video ID: {video_id} (Scheduled at: {publish_at_rfc3339})")

            # Upload custom thumbnail if present
            if thumbnail_path and thumbnail_path.exists():
                try:
                    logger.info(f"Setting custom thumbnail for video {video_id}...")
                    service.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
                    ).execute()
                    logger.info("Custom thumbnail uploaded successfully.")
                except Exception as thumb_err:
                    logger.warning(f"Failed to set custom thumbnail: {thumb_err} (Video upload remains scheduled)")

            return True, video_id, f"Video scheduled successfully for {publish_at_rfc3339}."

        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return False, "", f"Upload execution failed: {e}"
