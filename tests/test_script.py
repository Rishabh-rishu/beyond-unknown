"""
Unit tests for Script JSON Parsing, Pydantic Schema Validation, and Structure.
"""

import pytest
from pydantic import ValidationError
from ai.script_generator import ShortScriptSchema, SceneItem

def test_script_schema_validation():
    valid_data = {
        "hook": "Socho! 2000 saal pehle bhi aisi machine exist karti thi?",
        "intro": "Aaj hum explore kar rahe hain Antikythera Mechanism.",
        "core_explanation": "Bronze gear wheels jo astronomical cycles calculate karte the.",
        "surprising_reveal": "X-ray tomography ne reveal kiya ki ye Olympic calendar predict karta tha!",
        "cta": "Aise hi duniya ke hidden secrets ke liye Beyond Unknown ko subscribe karo.",
        "estimated_duration_seconds": 44.0,
        "scenes": [
            {
                "scene_id": 1,
                "time_range": "0-3s",
                "narration_chunk": "Socho! 2000 saal pehle bhi aisi machine exist karti thi?",
                "visual_keywords": "antikythera mechanism bronze gear macro 4k",
                "on_screen_text": "2000-YEAR OLD COMPUTER",
                "highlight_words": ["2000-YEAR", "COMPUTER"],
                "layout_style": "archaeological_card",
                "camera_motion": "slow_zoom_in"
            }
        ],
        "youtube_title": "Duniya Ka Pehla Computer? 😱 #Shorts",
        "youtube_description": "Full documentary breakdown... #BeyondUnknown #UnknownFacts",
        "youtube_tags": ["Beyond Unknown", "Antikythera", "Shorts"],
        "thumbnail_text": "ANCIENT COMPUTER FOUND"
    }

    script = ShortScriptSchema.model_validate(valid_data)
    assert script.hook.startswith("Socho")
    assert len(script.scenes) == 1
    assert script.scenes[0].layout_style == "archaeological_card"
    assert "Beyond Unknown" in script.cta

def test_script_schema_missing_fields():
    # Missing scenes list
    invalid_data = {
        "hook": "Hook text",
        "intro": "Intro text"
    }
    with pytest.raises(ValidationError):
        ShortScriptSchema.model_validate(invalid_data)
