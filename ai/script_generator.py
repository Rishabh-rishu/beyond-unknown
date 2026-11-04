"""
BEYOND UNKNOWN - Hinglish Script and Scene Planning Engine
Generates:
- Curiosity-driven Hinglish documentary scripts
- Scene-by-scene visual cues, search keywords, layout styles, and camera movements
- Metadata for YouTube (title, description, tags, hashtags, thumbnail text)
Validated using Pydantic structured schemas.
"""

import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from config import settings
from ai.gemini_client import GeminiClient
from research.researcher import ResearchDossier

logger = logging.getLogger("beyond_unknown.script_generator")

class SceneItem(BaseModel):
    scene_id: int
    time_range: str = Field(description="Approximate timing, e.g. '0-3s', '3-7s'")
    narration_chunk: str = Field(description="The exact spoken Hinglish words for this scene")
    visual_keywords: str = Field(description="English search query for cinematic video/photos")
    on_screen_text: str = Field(description="Clean, mobile-safe fact card text (3-6 words max)")
    highlight_words: List[str] = Field(default_factory=list, description="Keywords to highlight in Antique Gold")
    layout_style: str = Field(
        default="clean_documentary",
        description="Visual layout style: 'archaeological_card', 'telemetry_hud', 'stat_card', 'timeline_card', 'clean_documentary'"
    )
    camera_motion: str = Field(
        default="slow_zoom_in",
        description="Camera movement: 'slow_zoom_in', 'slow_zoom_out', 'pan_left', 'pan_right'"
    )

class ShortScriptSchema(BaseModel):
    hook: str = Field(description="0-3s high-curiosity opening hook in Hinglish")
    intro: str = Field(description="3-10s context introducing the mystery or discovery")
    core_explanation: str = Field(description="10-25s deep dive into the verified facts and engineering/science")
    surprising_reveal: str = Field(description="25-38s the most shocking verified evidence or detail")
    cta: str = Field(
        default="Aise hi duniya ke hidden secrets ke liye Beyond Unknown ko subscribe karo.",
        description="Final natural subscription call-to-action"
    )
    estimated_duration_seconds: float = Field(default=42.0, description="Estimated duration (35-50s)")
    scenes: List[SceneItem] = Field(description="8 to 12 planned visual scenes")
    youtube_title: str = Field(description="Curiosity-driven title under 75 characters with #Shorts")
    youtube_description: str = Field(description="Description with short explanation, verified facts, sources, and hashtags")
    youtube_tags: List[str] = Field(description="Relevant search tags")
    thumbnail_text: str = Field(description="3-5 bold punchy words for thumbnail frame")

class ScriptGenerator:
    def __init__(self):
        self.gemini_client = GeminiClient()

    def generate_script(self, dossier: ResearchDossier, slot: str = "morning") -> ShortScriptSchema:
        """
        Generates a complete Hinglish documentary script and visual plan based on verified facts.
        """
        logger.info(f"Generating Hinglish script for topic [{dossier.topic_id}] '{dossier.topic}'...")

        # Select layout mood based on category
        cat_lower = dossier.category.lower()
        if "india" in cat_lower or "ancient" in cat_lower or "archaeolog" in cat_lower:
            preferred_layout = "archaeological_card"
        elif "space" in cat_lower or "science" in cat_lower:
            preferred_layout = "telemetry_hud"
        elif "nature" in cat_lower or "geography" in cat_lower:
            preferred_layout = "stat_card"
        else:
            preferred_layout = "clean_documentary"

        prompt = f"""
CHANNEL: BEYOND UNKNOWN
TAGLINE: DISCOVER WHAT THE WORLD HIDES.
SLOT: {slot.upper()}
TOPIC: {dossier.topic}
COUNTRY/REGION: {dossier.country}
CATEGORY: {dossier.category}
PREFERRED BASE LAYOUT: {preferred_layout}

VERIFIED FACTS (You MUST strictly base your script on these facts):
{json.dumps(dossier.verified_facts, indent=2)}

PRIMARY SOURCES:
{json.dumps(dossier.source_urls, indent=2)}

INSTRUCTIONS:
1. Language: Natural, engaging Hinglish (natural Hindi + English conversational mix in Latin script).
2. Tone: Mysterious, cinematic documentary narrator. Energetic but controlled and serious.
3. Structure:
   - 0-3s: Powerful curiosity hook. Vary opening hooks! Examples:
     * "Socho, hazaron saal pehle..."
     * "Ye sunne mein impossible lagta hai, lekin..."
     * "Duniya ke sabse bade scientists bhi is mystery ke aage haar maan chuke hain..."
     * "Ruko! Ek aisi jagah jo modern science ko challenge karti hai..."
     DO NOT say "Hello friends, welcome back".
   - 3-10s: Introduce the discovery/monument/phenomenon.
   - 10-25s: Explain the core verified mechanism or historical details.
   - 25-38s: Reveal the surprising verified detail.
   - 38-44s: CTA: "Aise hi duniya ke hidden secrets ke liye Beyond Unknown ko subscribe karo."
4. Total Spoken Word Count: Approximately 100-130 words (fits 35-50 seconds at 1.15x speed).
5. Visual Plan:
   - Provide 8 to 12 distinct scenes (scene change every 2-4 seconds).
   - Each scene must have:
     * Specific English visual search keywords (cinematic, vertical, 4k).
     * On-screen text: 3-5 bold words for a fact card.
     * Highlight words (1-2 important words to highlight in Antique Gold #D6B56D).
     * layout_style: Choose dynamically between 'archaeological_card', 'telemetry_hud', 'stat_card', 'timeline_card', 'clean_documentary' to ensure layout variety!
     * camera_motion: 'slow_zoom_in', 'slow_zoom_out', 'pan_left', 'pan_right'.
6. YouTube Metadata:
   - Title: Curiosity-driven, under 70 characters, ending with #Shorts.
   - Description: Short summary + 2-3 bulleted verified facts + source references + #BeyondUnknown #UnknownFacts #HiddenHistory #MysteryFacts + topic hashtags.
   - Thumbnail Text: 3-5 high-impact words.
"""

        system_instruction = (
            "You are the senior scriptwriter and cinematic director for the BEYOND UNKNOWN channel. "
            "Write authentic, captivating Hinglish documentary narration grounded strictly in verified evidence. "
            "Never invent facts or statistics. Design sophisticated visual scenes with perfect mobile alignment."
        )

        script: ShortScriptSchema = self.gemini_client.generate_structured_content(
            prompt=prompt,
            response_schema=ShortScriptSchema,
            system_instruction=system_instruction
        )

        # Ensure CTA is exact
        script.cta = "Aise hi duniya ke hidden secrets ke liye Beyond Unknown ko subscribe karo."
        
        logger.info(f"Script generated successfully: {len(script.scenes)} scenes, title: '{script.youtube_title}'")
        return script
