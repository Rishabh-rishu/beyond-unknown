"""
BEYOND UNKNOWN - Edge TTS Voiceover Engine
Synthesizes Hinglish documentary narration using Microsoft Edge TTS.
Extracts word-level timestamps for precise subtitle synchronization.
Includes retry logic, rate limit backoff, and offline fallback.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import settings

logger = logging.getLogger("beyond_unknown.voice.tts")

class TTSEngine:
    def __init__(self, voice_name: Optional[str] = None):
        self.voice_name = voice_name or settings.VOICE_NAME or "hi-IN-MadhurNeural"

    async def _synthesize_async(
        self,
        text: str,
        output_audio_path: Path,
        max_retries: int = 3
    ) -> List[Dict]:
        """
        Asynchronously synthesizes speech and collects word-boundary timing events.
        """
        import edge_tts

        word_events = []
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Synthesizing speech with voice '{self.voice_name}' (Attempt {attempt}/{max_retries})...")
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice_name
                )
                
                with open(output_audio_path, "wb") as f_out:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f_out.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            # chunk: {'type': 'WordBoundary', 'offset': 1000000 (100ns), 'duration': 2500000, 'text': 'Ruko'}
                            offset_sec = chunk["offset"] / 10_000_000.0
                            duration_sec = chunk["duration"] / 10_000_000.0
                            word_events.append({
                                "word": chunk["text"],
                                "start": offset_sec,
                                "end": offset_sec + duration_sec
                            })

                if output_audio_path.exists() and output_audio_path.stat().st_size > 1000:
                    logger.info(f"Audio synthesized successfully ({output_audio_path.stat().st_size} bytes, {len(word_events)} word cues).")
                    return word_events

            except Exception as e:
                last_error = e
                logger.warning(f"TTS attempt {attempt} failed: {e}")
                await asyncio.sleep(2.0 * attempt)

        logger.error(f"TTS failed after {max_retries} attempts: {last_error}. Generating offline fallback...")
        return self._generate_fallback_audio(text, output_audio_path)

    def _generate_fallback_audio(self, text: str, output_path: Path) -> List[Dict]:
        """
        Generates clean offline placeholder speech tone for testing without network.
        """
        import subprocess
        # Calculate approximate duration based on word count (130 wpm = ~2.1 words/sec)
        words = text.split()
        est_duration = max(5.0, len(words) / 2.3)

        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"sine=frequency=220:duration={est_duration:.1f}",
            "-af", "volume=0.2",
            "-c:a", "libmp3lame", str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        word_events = []
        time_per_word = est_duration / max(1, len(words))
        curr = 0.0
        for w in words:
            word_events.append({
                "word": w,
                "start": curr,
                "end": curr + time_per_word
            })
            curr += time_per_word
        return word_events

    def generate_narration(self, text: str, output_audio_path: Path) -> List[Dict]:
        """
        Synchronous entrypoint for TTS synthesis.
        Returns list of word-level timing dictionaries.
        """
        output_audio_path.parent.mkdir(parents=True, exist_ok=True)
        return asyncio.run(self._synthesize_async(text, output_audio_path))
