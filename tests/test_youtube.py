"""
Unit tests for YouTube Upload Metadata and Dry-Run Simulation.
"""

from pathlib import Path
import pytest
from youtube.uploader import YouTubeUploader

def test_dry_run_upload_returns_mock_id(tmp_path):
    uploader = YouTubeUploader()
    dummy_video = tmp_path / "test_short.mp4"
    dummy_video.write_bytes(b"dummy_mp4_bytes")

    success, video_id, msg = uploader.upload_and_schedule_short(
        video_path=dummy_video,
        thumbnail_path=None,
        title="Hidden Secret of Kailasa Temple #Shorts",
        description="Full explanation here...",
        tags=["Beyond Unknown", "Shorts"],
        publish_at_rfc3339="2026-11-05T04:00:00Z",
        dry_run=True
    )

    assert success is True
    assert "mock_yt_" in video_id
    assert "Dry-run upload simulation" in msg
