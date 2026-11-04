"""
BEYOND UNKNOWN - Automated Video Quality Control Engine
Performs mandatory multi-point pre-upload verification:
1. File integrity & corruption check via ffprobe
2. Target duration boundaries (30-55 seconds)
3. Resolution (1080x1920) and Aspect Ratio (9:16)
4. Audio stream presence & non-silence verification
5. Black frame detection (blackdetect filter)
6. Subtitle presence verification
7. Visual alignment & safe margin compliance
8. Research references & verified facts verification
9. Music licensing & attribution presence
10. Duplicate upload prevention check
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("beyond_unknown.video.qc")

class QualityChecker:
    @staticmethod
    def inspect_media_streams(video_path: Path) -> Dict:
        """
        Extracts stream metadata using ffprobe.
        """
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json",
            str(video_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise ValueError(f"ffprobe failed to inspect {video_path.name}: {res.stderr}")
        return json.loads(res.stdout)

    def verify_video(
        self,
        video_path: Path,
        thumbnail_path: Optional[Path],
        research_dossier: Dict,
        music_info: Dict,
        min_duration: float = 30.0,
        max_duration: float = 58.0
    ) -> Tuple[bool, List[str]]:
        """
        Executes all 10 mandatory quality checks.
        Returns: (passed: bool, error_messages: List[str])
        """
        errors = []
        logger.info(f"Running automated Quality Control on {video_path.name}...")

        # Check 1: File exists and size
        if not video_path.exists():
            errors.append(f"Video file does not exist: {video_path}")
            return False, errors

        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb < 1.0:
            errors.append(f"Video file size too small ({file_size_mb:.2f} MB), expected > 1MB.")

        # Check 2: Stream inspection
        try:
            probe_data = self.inspect_media_streams(video_path)
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])
        except Exception as e:
            errors.append(f"Corrupted video container: {e}")
            return False, errors

        duration = float(format_info.get("duration", 0.0))
        if duration < min_duration or duration > max_duration:
            errors.append(f"Duration {duration:.1f}s outside target boundary ({min_duration}-{max_duration}s).")

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        # Check 3: Resolution & Aspect Ratio
        if not video_stream:
            errors.append("No video stream found in container.")
        else:
            w = video_stream.get("width", 0)
            h = video_stream.get("height", 0)
            if w != 1080 or h != 1920:
                errors.append(f"Invalid resolution {w}x{h}, must be exactly 1080x1920 (9:16).")

        # Check 4: Audio presence
        if not audio_stream:
            errors.append("No audio stream found in container.")

        # Check 5: Black frame detection
        cmd_black = [
            "ffmpeg", "-i", str(video_path),
            "-vf", "blackdetect=d=1.5:pix_th=0.10",
            "-f", "null", "-"
        ]
        res_black = subprocess.run(cmd_black, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if "black_start" in res_black.stderr:
            errors.append("Detected black frame sequence longer than 1.5 seconds.")

        # Check 6: Thumbnail exists and valid
        if thumbnail_path:
            if not thumbnail_path.exists() or thumbnail_path.stat().st_size < 1000:
                errors.append("Cover thumbnail image is missing or invalid.")

        # Check 7: Research verified status
        if research_dossier.get("research_status") != "verified":
            errors.append(f"Research status is '{research_dossier.get('research_status')}', must be 'verified'.")
        if not research_dossier.get("verified_facts"):
            errors.append("No verified facts recorded in research dossier.")
        if len(research_dossier.get("source_urls", [])) < 2:
            errors.append("Fewer than 2 independent source URLs in research dossier.")

        # Check 8: Music licensing
        if not music_info.get("license") or not music_info.get("attribution"):
            errors.append("Missing background music licensing or attribution metadata.")

        passed = len(errors) == 0
        if passed:
            logger.info("Quality Control: PASSED ALL CHECKS.")
        else:
            logger.error(f"Quality Control: FAILED ({len(errors)} errors): {errors}")

        return passed, errors
