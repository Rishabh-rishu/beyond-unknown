"""
BEYOND UNKNOWN - Master Automated Video Production Pipeline
End-to-end coordinator for daily YouTube Shorts generation, validation, and scheduling.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
from config import settings
from ai.topic_generator import TopicManager
from research.researcher import Researcher, ResearchDossier
from ai.script_generator import ScriptGenerator, ShortScriptSchema
from voice.tts_engine import TTSEngine
from voice.audio_processor import AudioProcessor
from assets.asset_manager import AssetManager
from video.scene_planner import ScenePlanner
from video.subtitle_generator import SubtitleGenerator
from video.music_selector import MusicSelector
from video.video_editor import VideoEditor
from video.quality_checker import QualityChecker
from youtube.scheduler import PublishingScheduler
from youtube.uploader import YouTubeUploader
from automation.state_manager import StateManager, RunState
from automation.recovery import RecoveryManager

logger = logging.getLogger("beyond_unknown.pipeline")

class Pipeline:
    def __init__(self):
        self.topic_manager = TopicManager()
        self.researcher = Researcher()
        self.script_generator = ScriptGenerator()
        self.tts_engine = TTSEngine()
        self.audio_processor = AudioProcessor(speed=settings.AUDIO_TEMPO)
        self.asset_manager = AssetManager()
        self.scene_planner = ScenePlanner()
        self.subtitle_generator = SubtitleGenerator()
        self.music_selector = MusicSelector()
        self.video_editor = VideoEditor()
        self.quality_checker = QualityChecker()
        self.scheduler = PublishingScheduler()
        self.uploader = YouTubeUploader()
        self.state_manager = StateManager()
        self.recovery = RecoveryManager(self.state_manager)

    def run(
        self,
        slot: str,
        dry_run: bool = False,
        publish: bool = True
    ) -> Dict:
        """
        Executes complete production run for given slot ('morning' or 'evening').
        """
        slot = slot.lower()
        logger.info(f"=== STARTING BEYOND UNKNOWN PRODUCTION RUN (Slot: {slot.upper()}, Dry-Run: {dry_run}, Publish: {publish}) ===")

        # 1. State Management & Resumption check
        state, resume_stage = self.recovery.evaluate_resumption(slot)
        if not state:
            state = self.state_manager.create_run(slot)

        scratch_dir = settings.PROJECT_ROOT / "scratch" / state.run_id
        scratch_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 2. Topic Selection
            if not state.topic_id:
                topic = None
                max_topic_attempts = 5
                for _ in range(max_topic_attempts):
                    candidate = self.topic_manager.get_next_topic(slot=slot)
                    if not candidate:
                        raise RuntimeError(f"No available topics found for slot '{slot}'.")

                    # Check research verification
                    dossier = self.researcher.research_topic(candidate)
                    if dossier.research_status == "verified":
                        topic = candidate
                        state.dossier_data = dossier.model_dump()
                        break
                    else:
                        logger.warning(f"Rejecting candidate topic '{candidate.get('title')}' due to failed fact verification.")
                        self.topic_manager.mark_rejected(candidate.get("id"), "Failed factual verification")

                if not topic:
                    raise RuntimeError("Could not find a factually verified topic after multiple attempts.")

                state.topic_id = topic["id"]
                state.topic_title = topic["title"]
                state.category = topic["category"]
                state.current_stage = "TOPIC_SELECTED"
                self.state_manager.save_state(state)

            dossier = ResearchDossier.model_validate(state.dossier_data)

            # 3. Script Generation
            if not state.script_data:
                script = self.script_generator.generate_script(dossier=dossier, slot=slot)
                state.script_data = script.model_dump()
                state.current_stage = "SCRIPT_GENERATED"
                self.state_manager.save_state(state)

                # Save script JSON to output/scripts/
                script_path = settings.SCRIPTS_OUTPUT_DIR / f"{state.topic_id}_{state.run_id}.json"
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(state.script_data, f, indent=2, ensure_ascii=False)

            script = ShortScriptSchema.model_validate(state.script_data)

            # 4. Voiceover Generation & 1.15x Speedup
            if not state.processed_audio_path or not Path(state.processed_audio_path).exists():
                raw_audio_path = scratch_dir / "raw_narration.mp3"
                processed_audio_path = settings.AUDIO_OUTPUT_DIR / f"{state.topic_id}_{state.run_id}_115x.mp3"

                full_narration_text = f"{script.hook} {script.intro} {script.core_explanation} {script.surprising_reveal} {script.cta}"
                word_cues = self.tts_engine.generate_narration(full_narration_text, raw_audio_path)

                proc_path, dur, scaled_cues = self.audio_processor.process_narration_audio(
                    raw_audio_path=raw_audio_path,
                    processed_audio_path=processed_audio_path,
                    word_cues=word_cues
                )

                state.raw_audio_path = str(raw_audio_path)
                state.processed_audio_path = str(proc_path)
                state.audio_duration = dur
                state.word_cues = scaled_cues
                state.current_stage = "VOICE_COMPLETED"
                self.state_manager.save_state(state)

            # 5. Visual Asset Acquisition & Dynamic Composition
            if not state.scenes_data:
                run_assets_dir = scratch_dir / "assets"
                scenes_data, licenses = self.asset_manager.acquire_scene_assets(
                    script=script,
                    topic_title=state.topic_title,
                    category=state.category,
                    run_assets_dir=run_assets_dir
                )
                state.scenes_data = scenes_data
                state.current_stage = "ASSETS_ACQUIRED"
                self.state_manager.save_state(state)

            # 6. Scene Planning & ASS Subtitle Generation
            planned_scenes = self.scene_planner.calculate_scene_timings(
                scenes_data=state.scenes_data,
                total_audio_duration=state.audio_duration
            )

            if not state.subtitles_ass_path or not Path(state.subtitles_ass_path).exists():
                ass_path = scratch_dir / "subtitles.ass"
                # Collect highlight words from all scenes
                all_highlights = []
                for sc in script.scenes:
                    all_highlights.extend(sc.highlight_words)

                self.subtitle_generator.build_ass_subtitles(
                    word_cues=state.word_cues or [],
                    output_ass_path=ass_path,
                    total_duration=state.audio_duration,
                    highlight_keywords=all_highlights
                )
                state.subtitles_ass_path = str(ass_path)
                self.state_manager.save_state(state)

            # 7. Music Selection
            if not state.music_info:
                state.music_info = self.music_selector.select_track_for_topic(category=state.category)
                self.state_manager.save_state(state)

            # 8. Video Production (FFmpeg Assembly)
            if not state.video_output_path or not Path(state.video_output_path).exists():
                output_video_path = settings.VIDEOS_OUTPUT_DIR / f"{state.topic_id}_{slot}.mp4"
                final_video_path, thumb_path = self.video_editor.assemble_final_video(
                    planned_scenes=planned_scenes,
                    narration_audio_path=Path(state.processed_audio_path),
                    music_info=state.music_info,
                    subtitles_ass_path=Path(state.subtitles_ass_path),
                    output_video_path=output_video_path,
                    scratch_dir=scratch_dir
                )
                state.video_output_path = str(final_video_path)
                state.thumbnail_path = str(thumb_path)
                state.current_stage = "VIDEO_RENDERED"
                self.state_manager.save_state(state)

            # 9. Automated Quality Control Verification
            qc_ok, qc_errors = self.quality_checker.verify_video(
                video_path=Path(state.video_output_path),
                thumbnail_path=Path(state.thumbnail_path) if state.thumbnail_path else None,
                research_dossier=state.dossier_data,
                music_info=state.music_info
            )
            state.qc_passed = qc_ok

            if not qc_ok:
                state.error_message = f"Quality control failed: {'; '.join(qc_errors)}"
                self.state_manager.save_state(state)
                raise ValueError(state.error_message)

            state.current_stage = "QC_PASSED"
            self.state_manager.save_state(state)

            # 10. Dynamic Scheduling & YouTube Upload
            target_utc, rfc3339_str, buffer_ok, sched_msg = self.scheduler.calculate_publish_time(slot=slot)
            state.publish_at_rfc3339 = rfc3339_str

            if not buffer_ok:
                logger.warning(f"Scheduling buffer check warning: {sched_msg}")

            if publish:
                upload_ok, yt_id, upload_msg = self.uploader.upload_and_schedule_short(
                    video_path=Path(state.video_output_path),
                    thumbnail_path=Path(state.thumbnail_path) if state.thumbnail_path else None,
                    title=script.youtube_title,
                    description=script.youtube_description,
                    tags=script.youtube_tags,
                    publish_at_rfc3339=rfc3339_str,
                    dry_run=dry_run
                )

                if not upload_ok:
                    state.error_message = f"YouTube upload failed: {upload_msg}"
                    self.state_manager.save_state(state)
                    raise RuntimeError(state.error_message)

                state.youtube_video_id = yt_id
                state.current_stage = "UPLOADED"
                self.state_manager.save_state(state)

                # Mark in published tracker
                self.topic_manager.mark_published(
                    topic_id=state.topic_id,
                    youtube_video_id=yt_id,
                    publish_at_utc=rfc3339_str,
                    title=script.youtube_title
                )

            logger.info(f"=== BEYOND UNKNOWN PRODUCTION RUN COMPLETED SUCCESSFULLY [{state.run_id}] ===")
            return {
                "status": "SUCCESS",
                "run_id": state.run_id,
                "slot": slot,
                "topic_id": state.topic_id,
                "title": script.youtube_title,
                "video_path": state.video_output_path,
                "thumbnail_path": state.thumbnail_path,
                "publish_at_utc": state.publish_at_rfc3339,
                "youtube_video_id": state.youtube_video_id,
                "dry_run": dry_run
            }

        except Exception as e:
            state.error_message = str(e)
            self.state_manager.save_state(state)
            logger.error(f"Pipeline execution failed for {state.run_id}: {e}", exc_info=True)
            return {
                "status": "FAILED",
                "run_id": state.run_id,
                "slot": slot,
                "error": str(e),
                "last_stage": state.current_stage
            }
