"""
BEYOND UNKNOWN - Subtitle Generation Engine
Generates styled Advanced SubStation Alpha (ASS) and SRT subtitles.
Features:
- Word-level timestamp synchronization (scaled to 1.15x audio)
- Mobile safe-area vertical placement (MarginV: 420)
- Bold white typography with Antique Gold (&H006DB5D6&) keyword highlighting
- Unicode support for flawless Devanagari and Latin script
- Short, punchy chunks (3-5 words per cue)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from config import settings

logger = logging.getLogger("beyond_unknown.video.subtitles")

class SubtitleGenerator:
    def __init__(self):
        self.brand = settings.get_brand_config()

    @staticmethod
    def _format_ass_timestamp(seconds: float) -> str:
        """Converts float seconds to ASS format: H:MM:SS.cs"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        """Converts float seconds to SRT format: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int(round((seconds - int(seconds)) * 1000))
        if millisecs >= 1000:
            millisecs = 999
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def build_ass_subtitles(
        self,
        word_cues: List[Dict],
        output_ass_path: Path,
        total_duration: float,
        highlight_keywords: Optional[List[str]] = None
    ) -> Path:
        """
        Creates a beautifully styled .ass subtitle file with antique gold highlights.
        """
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        norm_highlights = [h.strip().lower() for h in (highlight_keywords or [])]

        # Group words into short 3-5 word clusters
        clusters = []
        if word_cues:
            chunk = []
            words_per_cue = 4
            for cue in word_cues:
                chunk.append(cue)
                if len(chunk) >= words_per_cue:
                    clusters.append({
                        "start": chunk[0]["start"],
                        "end": chunk[-1]["end"],
                        "words": [c["word"] for c in chunk]
                    })
                    chunk = []
            if chunk:
                clusters.append({
                    "start": chunk[0]["start"],
                    "end": chunk[-1]["end"],
                    "words": [c["word"] for c in chunk]
                })
        else:
            # Fallback if no word cues available: generate dummy spaced cues
            clusters = [{
                "start": 0.0,
                "end": min(5.0, total_duration),
                "words": ["BEYOND", "UNKNOWN", "DISCOVER"]
            }]

        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,54,&H00FFFFFF,&H006DB5D6,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,90,90,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for cluster in clusters:
            start_str = self._format_ass_timestamp(cluster["start"])
            end_str = self._format_ass_timestamp(cluster["end"])
            
            # Format text with gold color override tag for highlight keywords
            # ASS color format: \\c&HBBGGRR& (Antique Gold #D6B56D = B:0x6D, G:0xB5, R:0xD6 -> &H6DB5D6&)
            formatted_words = []
            for w in cluster["words"]:
                clean = w.strip(" ,.!?\":;'").lower()
                if clean in norm_highlights or any(h in clean for h in norm_highlights):
                    formatted_words.append(f"{{\\c&H6DB5D6&}}{w}{{\\c&HFFFFFF&}}")
                else:
                    formatted_words.append(w)

            text_line = " ".join(formatted_words)
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_line}")

        full_ass_content = ass_header + "\n".join(events) + "\n"

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(full_ass_content)

        logger.info(f"Generated ASS subtitles ({len(clusters)} cues) at {output_ass_path.name}")
        return output_ass_path
