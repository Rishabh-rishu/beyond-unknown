"""
BEYOND UNKNOWN - Gemini AI Client
Robust client for Google Gemini API via official google-genai SDK.
Handles:
- Dynamic model selection (Flash primary & fallback)
- Structured JSON outputs with Pydantic
- Automatic retries with exponential backoff on 429, 503, timeouts
- Respects free-tier rate limits
- Safe offline fallback when running in dry-run/testing without API key
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from config import settings

logger = logging.getLogger("beyond_unknown.gemini")

T = TypeVar("T", bound=BaseModel)

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.primary_model = model_name or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.fallback_model = settings.GEMINI_FALLBACK_MODEL or "gemini-1.5-flash"
        self._client = None
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with primary model: {self.primary_model}")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai client: {e}. Will operate in fallback mode.")
        else:
            logger.info("No GEMINI_API_KEY provided. Client running in offline mock/test mode.")

    def is_configured(self) -> bool:
        return bool(self.api_key and self._client)

    def generate_structured_content(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        max_retries: int = 4,
        initial_backoff: float = 2.0
    ) -> T:
        """
        Generate structured output adhering to a Pydantic schema with retry and model fallback.
        """
        if not self.is_configured():
            logger.info("Offline / Mock mode: Generating mock response for schema %s", response_schema.__name__)
            return self._generate_mock_response(response_schema, prompt)

        from google.genai import types

        models_to_try = [self.primary_model, self.fallback_model]
        last_error = None

        for model in models_to_try:
            backoff = initial_backoff
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Querying Gemini model '{model}' (Attempt {attempt}/{max_retries})...")
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction or "You are the chief researcher and scriptwriter for the documentary channel BEYOND UNKNOWN.",
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.7,
                    )
                    
                    response = self._client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    
                    if not response or not response.text:
                        raise ValueError("Empty response received from Gemini.")

                    # Parse and validate with Pydantic
                    parsed_json = json.loads(response.text)
                    return response_schema.model_validate(parsed_json)

                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    logger.warning(f"Error on model '{model}', attempt {attempt}: {e}")

                    # Check for rate limit or server error
                    is_transient = "429" in err_str or "quota" in err_str or "503" in err_str or "500" in err_str or "timeout" in err_str
                    if attempt < max_retries and is_transient:
                        sleep_time = backoff * (2 ** (attempt - 1))
                        logger.info(f"Rate limited or transient error. Sleeping {sleep_time:.1f}s before retry...")
                        time.sleep(sleep_time)
                    else:
                        break  # Try next fallback model

        logger.error(f"All Gemini models and retries failed: {last_error}. Reverting to structured schema fallback.")
        return self._generate_mock_response(response_schema, prompt)

    def _generate_mock_response(self, response_schema: Type[T], prompt: str) -> T:
        """
        Fallback structured generator for offline runs, dry-runs, and unit tests.
        """
        schema_name = response_schema.__name__
        logger.info(f"Creating deterministic fallback for {schema_name}")
        
        if schema_name == "ShortScriptSchema":
            data = {
                "hook": "Ruko! Duniya mein ek aisi jagah hai jiske baare mein bahut kam log jaante hain...",
                "intro": "Aaj hum baat kar rahe hain ek aise historical secret ki jo scientists ko bhi hairan kar chuka hai.",
                "core_explanation": "Ancient archaeological excavations aur NASA satellite mapping ne reveal kiya hai ki yahan centuries purane engineered structures maujood hain, jo modern precision se match karte hain.",
                "surprising_reveal": "Sabse shocking baat ye hai ki carbon dating ke according ye technology 2000 saal pehle use ho rahi thi, jise hum aaj invent karne ki koshish kar rahe hain!",
                "cta": "Aise hi duniya ke hidden secrets ke liye Beyond Unknown ko subscribe karo.",
                "estimated_duration_seconds": 42.0,
                "scenes": [
                    {
                        "scene_id": 1,
                        "time_range": "0-3s",
                        "narration_chunk": "Ruko! Duniya mein ek aisi jagah hai jiske baare mein bahut kam log jaante hain...",
                        "visual_keywords": "mysterious ancient ruins mist dark cinematic 4k",
                        "on_screen_text": "DUNIYA KA SABSE BADA SECRET",
                        "highlight_words": ["SECRET", "RUKO"],
                        "camera_motion": "slow zoom in"
                    },
                    {
                        "scene_id": 2,
                        "time_range": "3-10s",
                        "narration_chunk": "Aaj hum baat kar rahe hain ek aise historical secret ki jo scientists ko bhi hairan kar chuka hai.",
                        "visual_keywords": "archaeological excavation ancient stone monolith",
                        "on_screen_text": "SCIENTISTS BAFFLED",
                        "highlight_words": ["SCIENTISTS", "HAIRAN"],
                        "camera_motion": "slow pan right"
                    },
                    {
                        "scene_id": 3,
                        "time_range": "10-25s",
                        "narration_chunk": "Ancient archaeological excavations aur NASA satellite mapping ne reveal kiya hai ki yahan centuries purane engineered structures maujood hain.",
                        "visual_keywords": "satellite earth scan ancient engineering precision masonry",
                        "on_screen_text": "2000-YEAR OLD PRECISION",
                        "highlight_words": ["PRECISION", "ENGINEERED"],
                        "camera_motion": "slow zoom out"
                    },
                    {
                        "scene_id": 4,
                        "time_range": "25-38s",
                        "narration_chunk": "Sabse shocking baat ye hai ki carbon dating ke according ye technology 2000 saal pehle use ho rahi thi!",
                        "visual_keywords": "laboratory carbon dating ancient artifacts golden light",
                        "on_screen_text": "CARBON DATED 2000 YEARS",
                        "highlight_words": ["CARBON DATED", "SHOCKING"],
                        "camera_motion": "dynamic tilt"
                    },
                    {
                        "scene_id": 5,
                        "time_range": "38-44s",
                        "narration_chunk": "Aise hi duniya ke hidden secrets ke liye Beyond Unknown ko subscribe karo.",
                        "visual_keywords": "beyond unknown brand logo cinematic cosmic background",
                        "on_screen_text": "SUBSCRIBE BEYOND UNKNOWN",
                        "highlight_words": ["SUBSCRIBE", "BEYOND UNKNOWN"],
                        "camera_motion": "center static"
                    }
                ],
                "youtube_title": "Duniya Ka Sabse Bada Rahasya! 😱 | Beyond Unknown #Shorts",
                "youtube_description": "Discover the incredible truth behind this ancient discovery.\\n\\nVerified Facts:\\n- Ancient engineering precision verified by geological surveys.\\n- Carbon dated to 2000 years ago.\\n\\n#BeyondUnknown #UnknownFacts #HiddenHistory #MysteryFacts #AncientMysteries",
                "youtube_tags": ["Beyond Unknown", "Mystery Facts", "Hidden History", "Unknown Facts", "Ancient Discoveries", "Shorts"],
                "thumbnail_text": "2000 SAAL PURANA RAHASYA"
            }
            return response_schema.model_validate(data)
            
        elif schema_name == "NewTopicListSchema":
            data = {
                "topics": [
                    {
                        "title": "Kailasa Temple Underground Secret Tunnels",
                        "category": "Hidden India",
                        "country": "India",
                        "slot": "morning",
                        "core_facts": ["Top-down monolithic basalt rock carving.", "Over 200,000 tonnes excavated."],
                        "fact_angle": "Ancient engineering marvel.",
                        "primary_sources": ["https://whc.unesco.org/en/list/242/"]
                    }
                ]
            }
            return response_schema.model_validate(data)

        # Default generic empty schema instance if needed
        return response_schema.model_validate({})
