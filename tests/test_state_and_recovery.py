"""
Unit tests for State Management and Failure Recovery.
"""

from pathlib import Path
import pytest
from automation.state_manager import StateManager, RunState
from automation.recovery import RecoveryManager

def test_state_persistence(tmp_path):
    sm = StateManager(checkpoints_dir=tmp_path)
    state = sm.create_run(slot="morning")
    assert state.slot == "morning"
    assert state.current_stage == "INIT"

    # Advance state
    state.topic_id = "BU-IND-001"
    state.current_stage = "TOPIC_SELECTED"
    sm.save_state(state)

    # Reload state
    reloaded = sm.load_state(state.run_id)
    assert reloaded is not None
    assert reloaded.topic_id == "BU-IND-001"
    assert reloaded.current_stage == "TOPIC_SELECTED"

def test_recovery_evaluation(tmp_path):
    sm = StateManager(checkpoints_dir=tmp_path)
    recovery = RecoveryManager(sm)

    # Empty state: should return NEW
    state, stage = recovery.evaluate_resumption("morning")
    assert state is None
    assert stage == "NEW"

    # Create incomplete state with existing completed video file
    dummy_video = tmp_path / "completed_video.mp4"
    dummy_video.write_bytes(b"0" * (2 * 1024 * 1024))  # 2MB

    run_state = sm.create_run(slot="morning")
    run_state.video_output_path = str(dummy_video)
    run_state.current_stage = "VIDEO_RENDERED"
    sm.save_state(run_state)

    # Resumption check should identify completed video and jump to UPLOAD
    resumed, stage = recovery.evaluate_resumption("morning")
    assert resumed is not None
    assert stage == "UPLOAD"
