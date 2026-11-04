"""
BEYOND UNKNOWN - YouTube Dynamic Publishing Scheduler
Calculates dynamically scheduled publishAt timestamps in Asia/Kolkata (IST),
converts them to UTC RFC 3339 format, handles UTC date rollovers,
and verifies minimum buffer requirements to prevent missed scheduling.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
from config import settings

logger = logging.getLogger("beyond_unknown.youtube.scheduler")

class PublishingScheduler:
    def __init__(self, tz_name: Optional[str] = None):
        self.tz_name = tz_name or settings.TIMEZONE or "Asia/Kolkata"
        self.tz = ZoneInfo(self.tz_name)
        self.morning_time_str = settings.MORNING_PUBLISH_TIME or "09:30"
        self.evening_time_str = settings.EVENING_PUBLISH_TIME or "17:30"
        self.buffer_minutes = settings.SCHEDULING_BUFFER_MINUTES or 45

    def calculate_publish_time(
        self,
        slot: str,
        current_time_utc: Optional[datetime] = None
    ) -> Tuple[datetime, str, bool, str]:
        """
        Dynamically calculates target publishing time for the given slot ('morning' or 'evening').
        Returns:
            (publish_datetime_utc, publish_at_rfc3339_string, is_buffer_sufficient, status_message)
        """
        now_utc = current_time_utc or datetime.now(timezone.utc)
        now_local = now_utc.astimezone(self.tz)

        # Parse target hour and minute for slot
        slot_lower = slot.lower()
        if slot_lower == "morning":
            target_str = self.morning_time_str
        elif slot_lower == "evening":
            target_str = self.evening_time_str
        else:
            target_str = self.morning_time_str

        t_parts = target_str.split(":")
        target_hour = int(t_parts[0])
        target_minute = int(t_parts[1])

        # Candidate slot time today in local timezone
        candidate_local = now_local.replace(
            hour=target_hour,
            minute=target_minute,
            second=0,
            microsecond=0
        )

        # Buffer threshold in minutes
        min_allowed_time = now_local + timedelta(minutes=self.buffer_minutes)

        # If candidate slot is already in the past or within buffer window,
        # schedule for tomorrow's occurrence of this slot!
        if candidate_local < min_allowed_time:
            target_local = candidate_local + timedelta(days=1)
            reason = f"Today's {slot} slot ({target_str} IST) is within the {self.buffer_minutes}m buffer or past. Scheduled for tomorrow."
        else:
            target_local = candidate_local
            reason = f"Scheduled for today's {slot} slot at {target_str} IST."

        # Convert local target time to UTC
        target_utc = target_local.astimezone(timezone.utc)
        
        # YouTube Data API requires RFC 3339 format: YYYY-MM-DDTHH:MM:SSZ
        rfc3339_str = target_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Double check buffer in UTC
        minutes_until_publish = (target_utc - now_utc).total_seconds() / 60.0
        buffer_ok = minutes_until_publish >= self.buffer_minutes

        logger.info(
            f"Scheduling: Slot={slot.upper()} | Target Local: {target_local.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
            f"Target UTC: {rfc3339_str} ({minutes_until_publish:.1f}m buffer) | {reason}"
        )

        return target_utc, rfc3339_str, buffer_ok, reason
