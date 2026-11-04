"""
Unit tests for Topic Management, Deduplication, and Slot Filtering.
"""

import pytest
from ai.topic_generator import TopicManager

def test_topic_deduplication():
    tm = TopicManager()
    existing = [
        {"id": "BU-IND-001", "title": "Kailasa Temple Ellora Single Rock Excavation"},
        {"id": "BU-GLO-001", "title": "Voynich Manuscript Cryptographic Analysis"}
    ]

    # Exact duplicate
    is_dup, reason = tm.is_duplicate("Kailasa Temple Ellora Single Rock Excavation", existing)
    assert is_dup is True
    assert "Exact match" in reason

    # Normalized duplicate (different case & extra spaces)
    is_dup, reason = tm.is_duplicate("  kailasa temple ellora single rock excavation! ", existing)
    assert is_dup is True

    # High token similarity duplicate
    is_dup, reason = tm.is_duplicate("Kailasa Temple Ellora Basalt Excavation", existing)
    assert is_dup is True
    assert "token similarity" in reason.lower()

    # Completely new topic
    is_dup, reason = tm.is_duplicate("Quantum Computing Entangled Photons", existing)
    assert is_dup is False

def test_slot_filtering():
    tm = TopicManager()
    morning_topics = tm.list_remaining_topics(slot="morning")
    evening_topics = tm.list_remaining_topics(slot="evening")

    assert len(morning_topics) > 0
    assert len(evening_topics) > 0

    for t in morning_topics:
        assert t["slot"] == "morning"
        assert t["category"] in ["Hidden India", "Ancient history and technology"]

    for t in evening_topics:
        assert t["slot"] == "evening"
        assert t["category"] in ["Global mysteries", "Science and space", "Strange nature and geography"]

def test_duplicate_upload_prevention(tmp_path):
    tm = TopicManager(data_dir=tmp_path)
    
    # Initialize mock files
    topics = [
        {"id": "TEST-001", "title": "Test Topic 1", "slot": "morning", "category": "Hidden India"}
    ]
    tm._save_json(tm.topics_file, topics)
    tm._save_json(tm.published_file, [])
    tm._save_json(tm.rejected_file, [])

    # First time: available
    rem = tm.list_remaining_topics(slot="morning")
    assert len(rem) == 1
    assert rem[0]["id"] == "TEST-001"

    # Mark published
    tm.mark_published("TEST-001", "yt_12345", "2026-11-05T04:00:00Z", "Test Video")

    # Second time: excluded
    rem_after = tm.list_remaining_topics(slot="morning")
    assert len(rem_after) == 0
    assert "TEST-001" in tm.get_published_ids()
