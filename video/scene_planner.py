"""
BEYOND UNKNOWN - Scene Planner
Calculates per-scene display durations, synchronizing visual cuts
with narration duration and speech segments.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("beyond_unknown.video.planner")

class ScenePlanner:
    @staticmethod
    def calculate_scene_timings(
        scenes_data: List[Dict],
        total_audio_duration: float
    ) -> List[Dict]:
        """
        Calculates exact start time and duration for each scene,
        ensuring total visual duration perfectly matches total audio duration.
        """
        num_scenes = len(scenes_data)
        if num_scenes == 0:
            return []

        # Base duration per scene
        base_dur = total_audio_duration / num_scenes
        current_start = 0.0

        planned_scenes = []
        for i, sc in enumerate(scenes_data):
            # Last scene absorbs any rounding remainder
            if i == num_scenes - 1:
                dur = total_audio_duration - current_start
            else:
                dur = base_dur

            planned_scenes.append({
                "scene_id": sc.get("scene_id", i + 1),
                "image_path": sc.get("image_path"),
                "camera_motion": sc.get("camera_motion", "slow_zoom_in"),
                "start_time": current_start,
                "duration": dur,
                "narration_chunk": sc.get("narration_chunk", "")
            })
            current_start += dur

        logger.info(f"Planned {num_scenes} scenes spanning {total_audio_duration:.2f}s (avg {base_dur:.2f}s per scene)")
        return planned_scenes
