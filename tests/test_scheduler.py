"""
Unit tests for Publishing Scheduling and Timezone Conversions.
"""

from datetime import datetime, timezone
import pytest
from zoneinfo import ZoneInfo
from youtube.scheduler import PublishingScheduler

def test_morning_slot_maps_to_0930_ist():
    scheduler = PublishingScheduler()
    # Mock current time at 07:00 AM IST on Nov 5, 2026 (01:30 UTC)
    ist = ZoneInfo("Asia/Kolkata")
    now_utc = datetime(2026, 11, 5, 1, 30, 0, tzinfo=timezone.utc)

    target_utc, rfc3339, buffer_ok, msg = scheduler.calculate_publish_time("morning", current_time_utc=now_utc)
    target_ist = target_utc.astimezone(ist)

    # Must be 09:30 AM IST today
    assert target_ist.hour == 9
    assert target_ist.minute == 30
    assert target_ist.day == 5

    # Converted to UTC: 09:30 IST - 5:30 = 04:00 UTC
    assert target_utc.hour == 4
    assert target_utc.minute == 0
    assert rfc3339 == "2026-11-05T04:00:00Z"
    assert buffer_ok is True

def test_evening_slot_maps_to_1730_ist():
    scheduler = PublishingScheduler()
    # Mock current time at 14:00 IST on Nov 5, 2026 (08:30 UTC)
    ist = ZoneInfo("Asia/Kolkata")
    now_utc = datetime(2026, 11, 5, 8, 30, 0, tzinfo=timezone.utc)

    target_utc, rfc3339, buffer_ok, msg = scheduler.calculate_publish_time("evening", current_time_utc=now_utc)
    target_ist = target_utc.astimezone(ist)

    # Must be 17:30 IST today
    assert target_ist.hour == 17
    assert target_ist.minute == 30
    assert target_ist.day == 5

    # Converted to UTC: 17:30 IST - 5:30 = 12:00 UTC
    assert target_utc.hour == 12
    assert target_utc.minute == 0
    assert rfc3339 == "2026-11-05T12:00:00Z"
    assert buffer_ok is True

def test_date_rollover_when_past_slot_time():
    scheduler = PublishingScheduler()
    # Mock current time at 10:00 AM IST on Nov 5 (already past 09:30 AM)
    ist = ZoneInfo("Asia/Kolkata")
    now_utc = datetime(2026, 11, 5, 4, 30, 0, tzinfo=timezone.utc)

    target_utc, rfc3339, buffer_ok, msg = scheduler.calculate_publish_time("morning", current_time_utc=now_utc)
    target_ist = target_utc.astimezone(ist)

    # Must roll over to tomorrow Nov 6 at 09:30 AM IST
    assert target_ist.day == 6
    assert target_ist.hour == 9
    assert target_ist.minute == 30
    assert rfc3339 == "2026-11-06T04:00:00Z"
    assert buffer_ok is True
