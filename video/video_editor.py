"""
BEYOND UNKNOWN - Complete FFmpeg Video Production Engine
Handles:
- Per-scene cinematic camera motions (slow zoom in, slow zoom out, slow pan)
- Video segment concatenation
- Audio mixing: full narration volume + ducked background music with smooth fades
- ASS subtitle burn-in with mobile safe margins and font directory resolution
- Broadcast output: 1080x1920, 9:16, 30 FPS, H.264, AAC
- Cover thumbnail frame extraction
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import settings

logger = logging.getLogger("beyond_unknown.video.editor")

class VideoEditor:
    def __init__(self):
        self.fonts_dir = settings.FONTS_DIR

    def render_scene_segment(
        self,
        image_path: str,
        duration: float,
        camera_motion: str,
        output_segment_path: Path,
        fps: int = 30
    ) -> Path:
        """
        Renders a single scene image into a 1080x1920 30fps MP4 video clip
        with smooth camera movement.
        """
        output_segment_path.parent.mkdir(parents=True, exist_ok=True)
        total_frames = max(30, int(round(duration * fps)))

        # Define smooth camera motion filter for 1080x1920
        # Zoom range is kept subtle (1.00 to 1.08) to maintain image crispness and text sharpness
        if camera_motion == "slow_zoom_out":
            vf = (
                f"zoompan=z='if(lte(zoom,1.0),1.08,max(1.001,zoom-0.0012))':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:s=1080x1920:fps={fps}"
            )
        elif camera_motion == "pan_left":
            vf = (
                f"zoompan=z='1.05':"
                f"x='if(lte(on,1),(iw-iw/zoom),max(0,x-1.5))':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:s=1080x1920:fps={fps}"
            )
        elif camera_motion == "pan_right":
            vf = (
                f"zoompan=z='1.05':"
                f"x='if(lte(on,1),0,min((iw-iw/zoom),x+1.5))':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:s=1080x1920:fps={fps}"
            )
        else:  # default slow_zoom_in
            vf = (
                f"zoompan=z='min(zoom+0.0012,1.08)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:s=1080x1920:fps={fps}"
            )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", vf,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            str(output_segment_path)
        ]

        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"Scene segment render failed for {image_path}: {res.stderr}")
            raise RuntimeError(f"FFmpeg segment error: {res.stderr[:200]}")

        return output_segment_path

    def assemble_final_video(
        self,
        planned_scenes: List[Dict],
        narration_audio_path: Path,
        music_info: Dict,
        subtitles_ass_path: Path,
        output_video_path: Path,
        scratch_dir: Path
    ) -> Tuple[Path, Path]:
        """
        Executes full production assembly:
        1. Renders all scene video segments
        2. Concatenates scene segments
        3. Mixes narration + ducked music
        4. Burns in styled ASS subtitles
        5. Extracts cover thumbnail frame
        Returns: (final_video_path, thumbnail_image_path)
        """
        scratch_dir.mkdir(parents=True, exist_ok=True)
        segments_dir = scratch_dir / "segments"
        segments_dir.mkdir(exist_ok=True)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting video assembly for {len(planned_scenes)} scenes...")

        # 1. Render all scene clips
        segment_paths = []
        for i, sc in enumerate(planned_scenes):
            seg_path = segments_dir / f"seg_{i:02d}.mp4"
            self.render_scene_segment(
                image_path=sc["image_path"],
                duration=sc["duration"],
                camera_motion=sc["camera_motion"],
                output_segment_path=seg_path
            )
            segment_paths.append(seg_path)

        # 2. Concatenate video clips
        concat_list_file = scratch_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in segment_paths:
                f.write(f"file '{p.resolve()}'\n")

        raw_concat_video = scratch_dir / "raw_concat.mp4"
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(raw_concat_video)
        ]
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Concatenated raw video created at {raw_concat_video.name}")

        # 3. Final composite pass: video + audio mix + ASS subtitles
        total_audio_dur = sum(sc["duration"] for sc in planned_scenes)
        duck_vol = music_info.get("ducking_volume", 0.12)
        fade_in = music_info.get("fade_in_seconds", 1.5)
        fade_out = music_info.get("fade_out_seconds", 2.0)
        fade_out_start = max(1.0, total_audio_dur - fade_out)
        music_path = music_info.get("file_path")

        # Complex audio filter: mix speech with ducked background music
        # and burn in ASS subtitles with custom fonts directory
        # Escape path for FFmpeg subtitles filter
        escaped_sub_path = str(subtitles_ass_path.resolve()).replace(":", "\\:").replace("'", "\\'")
        escaped_fonts_dir = str(self.fonts_dir.resolve()).replace(":", "\\:").replace("'", "\\'")
        video_filter = f"ass='{escaped_sub_path}':fontsdir='{escaped_fonts_dir}'"

        audio_filter = (
            f"[1:a]volume=1.0[vocal];"
            f"[2:a]volume={duck_vol:.2f},"
            f"afade=t=in:ss=0:d={fade_in:.1f},"
            f"afade=t=out:st={fade_out_start:.1f}:d={fade_out:.1f}[bg];"
            f"[vocal][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

        cmd_final = [
            "ffmpeg", "-y",
            "-i", str(raw_concat_video),
            "-i", str(narration_audio_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex", audio_filter,
            "-vf", video_filter,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video_path)
        ]

        logger.info(f"Running final composite render to {output_video_path.name}...")
        res_final = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_final.returncode != 0:
            logger.error(f"Final composite render failed: {res_final.stderr}")
            # If ASS filter fails on older system libraries, fallback to clean video without ASS
            logger.warning("Attempting fallback composite without ASS subtitles filter...")
            cmd_fallback = [
                "ffmpeg", "-y",
                "-i", str(raw_concat_video),
                "-i", str(narration_audio_path),
                "-stream_loop", "-1", "-i", str(music_path),
                "-filter_complex", audio_filter,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_video_path)
            ]
            subprocess.run(cmd_fallback, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        # 4. Extract Cover Thumbnail Frame (at ~2.5s)
        thumbnail_path = output_video_path.parent / (output_video_path.stem + "_thumb.jpg")
        thumb_time = min(2.5, total_audio_dur / 2.0)
        cmd_thumb = [
            "ffmpeg", "-y",
            "-ss", f"{thumb_time:.2f}",
            "-i", str(output_video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(thumbnail_path)
        ]
        subprocess.run(cmd_thumb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        logger.info(f"Production video generated successfully: {output_video_path.name} ({output_video_path.stat().st_size / (1024*1024):.2f} MB)")
        return output_video_path, thumbnail_path
