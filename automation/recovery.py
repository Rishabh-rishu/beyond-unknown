"""
BEYOND UNKNOWN - Failure Recovery Engine
Inspects previous run state and determines whether pipeline can resume
from an existing valid checkpoint (e.g. audio generated, video rendered).
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from automation.state_manager import RunState, StateManager

logger = logging.getLogger("beyond_unknown.automation.recovery")

class RecoveryManager:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def evaluate_resumption(self, slot: str) -> Tuple[Optional[RunState], str]:
        """
        Evaluates whether an incomplete run can be resumed safely.
        Returns: (resumable_state, resume_stage)
        """
        last_state = self.state_manager.find_latest_incomplete_run(slot)
        if not last_state:
            return None, "NEW"

        # Check if already rendered video file exists and is intact
        if last_state.video_output_path and Path(last_state.video_output_path).exists():
            if Path(last_state.video_output_path).stat().st_size > 1024 * 1024:
                logger.info(f"Recovery: Found completed video file for {last_state.run_id}. Resuming at QC/UPLOAD.")
                return last_state, "UPLOAD"

        # Check if processed audio exists
        if last_state.processed_audio_path and Path(last_state.processed_audio_path).exists():
            if Path(last_state.processed_audio_path).stat().st_size > 1000:
                logger.info(f"Recovery: Found completed audio file for {last_state.run_id}. Resuming at VIDEO_RENDER.")
                return last_state, "VIDEO_RENDER"

        logger.info(f"Recovery: Incomplete run {last_state.run_id} found with partial assets. Resuming from {last_state.current_stage}.")
        return last_state, last_state.current_stage
