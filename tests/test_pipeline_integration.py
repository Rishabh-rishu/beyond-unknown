"""
Integration tests for Pipeline Dry-Run and Fail-Safe Publishing Policies.
"""

from pathlib import Path
import pytest
from automation.pipeline import Pipeline

def test_pipeline_dry_run_morning():
    pipeline = Pipeline()
    
    # Run a complete dry-run for morning slot
    result = pipeline.run(slot="morning", dry_run=True, publish=True)
    
    assert result.get("status") == "SUCCESS"
    assert result.get("slot") == "morning"
    assert result.get("topic_id") is not None
    assert result.get("video_path") is not None
    assert Path(result["video_path"]).exists()
    assert Path(result["thumbnail_path"]).exists()
    assert "mock_yt_" in result.get("youtube_video_id")

def test_pipeline_failsafe_on_invalid_research(monkeypatch):
    pipeline = Pipeline()

    # Force researcher to return a rejected dossier
    from research.researcher import ResearchDossier
    rejected_dossier = ResearchDossier(
        topic_id="FAIL-001",
        topic="Unverified Claims",
        country="Global",
        category="Mystery",
        main_claims=["Unverified fake discovery"],
        verified_facts=[],
        uncertain_claims=["Unverified fake discovery"],
        source_urls=["https://invalid.com"],
        source_titles=["invalid"],
        research_status="rejected"
    )

    monkeypatch.setattr(pipeline.researcher, "research_topic", lambda topic: rejected_dossier)

    # When research fails on all candidate topics, pipeline must abort and NOT publish
    result = pipeline.run(slot="morning", dry_run=True, publish=True)
    assert result.get("status") == "FAILED"
    assert "factually verified" in result.get("error", "").lower()
