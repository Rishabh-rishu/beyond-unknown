"""
BEYOND UNKNOWN - Automation State Manager
Tracks stage-by-stage execution of a production run using persistent checkpoints.
Facilitates seamless resumption upon failure and ensures idempotent execution.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from config import settings

logger = logging.getLogger("beyond_unknown.automation.state")

class RunState(BaseModel):
    run_id: str
    slot: str  # "morning" or "evening"
    current_stage: str = "INIT"
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Topic data
    topic_id: Optional[str] = None
    topic_title: Optional[str] = None
    category: Optional[str] = None
    
    # Artifact paths
    dossier_data: Optional[Dict] = None
    script_data: Optional[Dict] = None
    raw_audio_path: Optional[str] = None
    processed_audio_path: Optional[str] = None
    audio_duration: Optional[float] = None
    word_cues: Optional[list] = None
    scenes_data: Optional[list] = None
    music_info: Optional[Dict] = None
    subtitles_ass_path: Optional[str] = None
    video_output_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    # Publishing details
    qc_passed: bool = False
    publish_at_rfc3339: Optional[str] = None
    youtube_video_id: Optional[str] = None
    error_message: Optional[str] = None

class StateManager:
    def __init__(self, checkpoints_dir: Optional[Path] = None):
        self.checkpoints_dir = checkpoints_dir or (settings.PROJECT_ROOT / "state_checkpoints")
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def generate_run_id(self, slot: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        import uuid
        short_id = uuid.uuid4().hex[:6]
        return f"run_{timestamp}_{slot.lower()}_{short_id}"

    def create_run(self, slot: str) -> RunState:
        run_id = self.generate_run_id(slot)
        state = RunState(run_id=run_id, slot=slot)
        self.save_state(state)
        logger.info(f"Initialized new production state: {run_id}")
        return state

    def get_checkpoint_path(self, run_id: str) -> Path:
        return self.checkpoints_dir / f"{run_id}.json"

    def save_state(self, state: RunState):
        state.updated_at_utc = datetime.now(timezone.utc).isoformat()
        chk_path = self.get_checkpoint_path(state.run_id)
        with open(chk_path, "w", encoding="utf-8") as f:
            json.dump(state.model_dump(), f, indent=2, ensure_ascii=False)

    def load_state(self, run_id: str) -> Optional[RunState]:
        chk_path = self.get_checkpoint_path(run_id)
        if chk_path.exists():
            try:
                with open(chk_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return RunState.model_validate(data)
            except Exception as e:
                logger.error(f"Error loading checkpoint {run_id}: {e}")
        return None

    def find_latest_incomplete_run(self, slot: str) -> Optional[RunState]:
        """Finds most recent incomplete run for the slot to allow resumption."""
        matching_files = sorted(self.checkpoints_dir.glob(f"*_{slot.lower()}_*.json"), reverse=True)
        for f in matching_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    state = RunState.model_validate(data)
                    # If not fully uploaded, it can potentially be resumed
                    if state.current_stage != "UPLOADED" and not state.youtube_video_id:
                        return state
            except Exception:
                continue
        return None
