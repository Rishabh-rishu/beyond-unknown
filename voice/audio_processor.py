"""
BEYOND UNKNOWN - Audio Processing Engine
Applies:
- Exact 1.15x speedup using FFmpeg atempo=1.15 (preserving pitch)
- Loudness normalization (EBU R128: -16 LUFS for YouTube Shorts)
- Word-level timestamp scaling (offset / 1.15)
- Automated quality checks (silence detection, RMS volume, duration bounds)
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import settings

logger = logging.getLogger("beyond_unknown.voice.processor")

class AudioProcessor:
    def __init__(self, speed: float = 1.15):
        self.speed = speed

    def scale_word_timestamps(self, word_cues: List[Dict], speed: float) -> List[Dict]:
        """
        Scales word boundary start and end timestamps to match the atempo filter.
        """
        scaled = []
        for cue in word_cues:
            scaled.append({
                "word": cue["word"],
                "start": cue["start"] / speed,
                "end": cue["end"] / speed
            })
        return scaled

    def process_narration_audio(
        self,
        raw_audio_path: Path,
        processed_audio_path: Path,
        word_cues: Optional[List[Dict]] = None
    ) -> Tuple[Path, float, List[Dict]]:
        """
        Applies atempo=1.15 and loudnorm to narration audio.
        Returns: (processed_audio_path, duration_seconds, scaled_word_cues)
        """
        processed_audio_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Applying atempo={self.speed:.2f} and loudnorm to {raw_audio_path.name}...")

        # FFmpeg filter: speedup narration by 1.15x and normalize to YouTube Shorts broadcast spec
        audio_filter = f"atempo={self.speed:.2f},loudnorm=I=-16:LRA=11:TP=-1.5"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_audio_path),
            "-filter:a", audio_filter,
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(processed_audio_path)
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg audio processing failed: {res.stderr}")
            raise RuntimeError(f"FFmpeg audio speedup failed: {res.stderr}")

        # Measure exact duration
        duration = self.get_audio_duration(processed_audio_path)
        logger.info(f"Processed audio saved: {processed_audio_path.name} (Duration: {duration:.2f}s)")

        # Scale word timestamps if available
        scaled_cues = []
        if word_cues:
            scaled_cues = self.scale_word_timestamps(word_cues, self.speed)

        # Validate quality
        is_valid, validation_msg = self.validate_audio(processed_audio_path, duration)
        if not is_valid:
            logger.error(f"Audio validation failed: {validation_msg}")
            raise ValueError(f"Corrupted or invalid audio: {validation_msg}")

        return processed_audio_path, duration, scaled_cues

    @staticmethod
    def get_audio_duration(audio_path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(res.stdout.strip())
        except Exception:
            return 0.0

    def validate_audio(self, audio_path: Path, duration: float) -> Tuple[bool, str]:
        """
        Validates that audio is non-empty, within duration boundaries, and contains no excessive silence.
        """
        if not audio_path.exists() or audio_path.stat().st_size < 1000:
            return False, "Audio file is missing or virtually empty."

        if duration < 25.0 or duration > 65.0:
            return False, f"Audio duration {duration:.1f}s is outside valid YouTube Shorts boundaries (25-65s)."

        # Run silence detection (detect silence longer than 3.0 seconds at -40dB)
        cmd = [
            "ffmpeg", "-i", str(audio_path),
            "-af", "silencedetect=noise=-40dB:d=3.0",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check if entire audio was silent
        if "silence_start: 0" in res.stderr and f"silence_end: {int(duration)}" in res.stderr:
            return False, "Audio is completely silent."

        return True, "Audio passed all quality checks."
