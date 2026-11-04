"""
Unit tests for Subtitle Generation and Mobile Safe-Area ASS Formatting.
"""

import pytest
from pathlib import Path
from video.subtitle_generator import SubtitleGenerator

def test_ass_timestamp_formatting():
    sg = SubtitleGenerator()
    assert sg._format_ass_timestamp(0.0) == "0:00:00.00"
    assert sg._format_ass_timestamp(65.42) == "0:01:05.42"
    assert sg._format_ass_timestamp(3605.12) == "1:00:05.12"

def test_srt_timestamp_formatting():
    sg = SubtitleGenerator()
    assert sg._format_srt_timestamp(0.0) == "00:00:00,000"
    assert sg._format_srt_timestamp(65.42) == "00:01:05,420"

def test_build_ass_subtitles_formatting(tmp_path):
    sg = SubtitleGenerator()
    cues = [
        {"word": "Ruko", "start": 0.0, "end": 0.5},
        {"word": "Ye", "start": 0.5, "end": 0.8},
        {"word": "SECRET", "start": 0.8, "end": 1.2},
        {"word": "hai", "start": 1.2, "end": 1.6}
    ]

    out_ass = tmp_path / "test.ass"
    sg.build_ass_subtitles(
        word_cues=cues,
        output_ass_path=out_ass,
        total_duration=10.0,
        highlight_keywords=["SECRET"]
    )

    assert out_ass.exists()
    content = out_ass.read_text(encoding="utf-8")

    # Check ASS Header properties
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "MarginV, Encoding" in content

    # Check Antique Gold highlight tag is present for the word SECRET
    # ASS tag: {\c&H6DB5D6&}
    assert r"{\c&H6DB5D6&}SECRET{\c&HFFFFFF&}" in content
