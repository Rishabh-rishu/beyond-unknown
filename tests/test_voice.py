"""
Unit tests for Voiceover Processing, 1.15x Speedup, and Timestamp Scaling.
"""

import pytest
from pathlib import Path
from voice.audio_processor import AudioProcessor

def test_timestamp_scaling():
    processor = AudioProcessor(speed=1.15)
    raw_cues = [
        {"word": "Ruko", "start": 0.0, "end": 0.5},
        {"word": "Duniya", "start": 0.5, "end": 1.15},
        {"word": "Secret", "start": 1.15, "end": 2.30}
    ]

    scaled = processor.scale_word_timestamps(raw_cues, speed=1.15)
    assert len(scaled) == 3
    assert scaled[0]["start"] == 0.0
    assert pytest.approx(scaled[1]["end"], 0.01) == 1.0  # 1.15 / 1.15 = 1.0
    assert pytest.approx(scaled[2]["end"], 0.01) == 2.0  # 2.30 / 1.15 = 2.0

def test_audio_duration_bounds():
    processor = AudioProcessor(speed=1.15)
    
    # Valid duration
    ok, msg = processor.validate_audio(Path(__file__), duration=42.0)
    # File exists check passes for __file__
    assert ok is True

    # Too short duration (< 25s)
    ok, msg = processor.validate_audio(Path(__file__), duration=15.0)
    assert ok is False
    assert "outside valid YouTube Shorts boundaries" in msg

    # Too long duration (> 65s)
    ok, msg = processor.validate_audio(Path(__file__), duration=75.0)
    assert ok is False
