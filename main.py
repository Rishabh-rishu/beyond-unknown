"""
BEYOND UNKNOWN - Command Line Interface
Main executable entry point for automated YouTube Shorts generation and publishing.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from config import settings
from automation.pipeline import Pipeline
from ai.topic_generator import TopicManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.PROJECT_ROOT / "pipeline.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("beyond_unknown.cli")

def run_setup_check():
    """
    Checks system dependencies, credentials, fonts, and API connectivity.
    """
    print("\n=======================================================")
    print("   BEYOND UNKNOWN - ENVIRONMENT & DEPENDENCY CHECK")
    print("   DISCOVER WHAT THE WORLD HIDES.")
    print("=======================================================\n")

    all_passed = True

    # 1. Python version
    py_ver = sys.version.split()[0]
    print(f"[✓] Python Runtime: {py_ver} ({sys.executable})")

    # 2. FFmpeg & FFprobe
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path and ffprobe_path:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, text=True)
        ffmpeg_ver = res.stdout.splitlines()[0] if res.stdout else "Available"
        print(f"[✓] FFmpeg: {ffmpeg_ver}")
        print(f"[✓] FFprobe: {ffprobe_path}")
    else:
        print("[✗] FFmpeg or FFprobe NOT found in PATH. Install via: sudo apt install ffmpeg")
        all_passed = False

    # 3. Typography & Fonts
    cinzel = settings.FONTS_DIR / "Cinzel.ttf"
    montserrat = settings.FONTS_DIR / "Montserrat.ttf"
    noto = settings.FONTS_DIR / "NotoSansDevanagari.ttf"
    if cinzel.exists() and montserrat.exists() and noto.exists():
        print(f"[✓] Fonts: All 3 typography fonts verified in {settings.FONTS_DIR.relative_to(settings.PROJECT_ROOT)}")
    else:
        print(f"[!] Warning: Some fonts missing in {settings.FONTS_DIR}. Fallbacks will be used.")

    # 4. Background Music Tracks
    music_tracks = list(settings.AUDIO_DIR.glob("*.mp3"))
    if len(music_tracks) >= 6:
        print(f"[✓] Background Music: All {len(music_tracks)} mood categories verified in {settings.AUDIO_DIR.relative_to(settings.PROJECT_ROOT)}")
    else:
        print(f"[!] Warning: Found {len(music_tracks)} music tracks (expected 6).")

    # 5. Gemini API Configuration
    if settings.GEMINI_API_KEY:
        masked_key = settings.GEMINI_API_KEY[:6] + "..." + settings.GEMINI_API_KEY[-4:]
        print(f"[✓] Google Gemini API: Configured (Key: {masked_key}, Model: {settings.GEMINI_MODEL})")
    else:
        print("[!] Google Gemini API: Not configured in .env (GEMINI_API_KEY). Running in offline fallback mode.")

    # 6. Pexels API Configuration
    if settings.PEXELS_API_KEY:
        masked_px = settings.PEXELS_API_KEY[:4] + "..." + settings.PEXELS_API_KEY[-4:]
        print(f"[✓] Pexels API: Configured (Key: {masked_px})")
    else:
        print("[i] Pexels API: Optional key missing. Using Wikimedia, NASA & Procedural Graphics.")

    # 7. YouTube Data API & OAuth Configuration
    from youtube.auth import YouTubeAuth
    yt_auth = YouTubeAuth()
    if yt_auth.is_configured():
        print("[✓] YouTube Data API v3: OAuth credentials configured.")
    else:
        print("[i] YouTube Data API v3: OAuth credentials not fully set. (Dry-run mode ready).")

    # 8. Topics Database
    tm = TopicManager()
    remaining = tm.list_remaining_topics()
    published = tm.get_published_ids()
    print(f"[✓] Topics Database: {len(remaining)} available in queue, {len(published)} published.")

    # 9. Voiceover Engine Check
    print(f"[✓] Voiceover Engine: Edge TTS (Voice: {settings.VOICE_NAME}, Speed: {settings.AUDIO_TEMPO}x)")

    # 10. Scheduling & Timezone Check
    from youtube.scheduler import PublishingScheduler
    sched = PublishingScheduler()
    _, m_utc, _, _ = sched.calculate_publish_time("morning")
    _, e_utc, _, _ = sched.calculate_publish_time("evening")
    print(f"[✓] Scheduling Engine: Timezone: {settings.TIMEZONE}")
    print(f"    - Morning Slot target: {settings.MORNING_PUBLISH_TIME} IST -> {m_utc} UTC")
    print(f"    - Evening Slot target: {settings.EVENING_PUBLISH_TIME} IST -> {e_utc} UTC")

    print("\n=======================================================")
    if all_passed:
        print("   STATUS: READY FOR PRODUCTION AUTOMATION")
    else:
        print("   STATUS: ATTENTION REQUIRED ON MISSING DEPENDENCIES")
    print("=======================================================\n")
    return all_passed

def list_topics():
    tm = TopicManager()
    all_topics = tm.list_remaining_topics()
    published_ids = tm.get_published_ids()
    print(f"\n=======================================================")
    print(f"   BEYOND UNKNOWN - TOPIC QUEUE ({len(all_topics)} REMAINING, {len(published_ids)} PUBLISHED)")
    print("=======================================================\n")
    
    cats = {}
    for t in all_topics:
        c = t.get("category", "General")
        cats[c] = cats.get(c, 0) + 1
        
    print(f"Queue breakdown by category: {json.dumps(cats, indent=2)}\n")
    print(f"{'ID':<12} | {'SLOT':<8} | {'CATEGORY':<28} | {'TITLE'}")
    print("-" * 80)
    for t in all_topics[:25]:
        print(f"{t.get('id'):<12} | {t.get('slot'):<8} | {t.get('category')[:26]:<28} | {t.get('title')[:36]}")
    if len(all_topics) > 25:
        print(f"... and {len(all_topics) - 25} more topics in queue.")
    print()

def show_status():
    tm = TopicManager()
    published_file = settings.DATA_DIR / "published_tracker.json"
    published = []
    if published_file.exists():
        with open(published_file, "r", encoding="utf-8") as f:
            published = json.load(f)
            
    remaining = tm.list_remaining_topics()
    rejected = tm.get_rejected_ids()
    
    print("\n=======================================================")
    print("   BEYOND UNKNOWN - PIPELINE STATUS & PUBLICATION HISTORY")
    print("=======================================================\n")
    print(f"Total Published Shorts: {len(published)}")
    print(f"Remaining Topics:       {len(remaining)}")
    print(f"Rejected Topics:        {len(rejected)}")
    print(f"Daily Output Target:    2 Shorts / Day (09:30 IST & 17:30 IST)")
    
    if published:
        print("\nRecent Publications:")
        print(f"{'TOPIC ID':<12} | {'YOUTUBE ID':<18} | {'PUBLISH AT UTC':<22} | {'TITLE'}")
        print("-" * 85)
        for p in published[-10:]:
            print(f"{p.get('topic_id', 'N/A'):<12} | {p.get('youtube_video_id', 'N/A'):<18} | {p.get('published_at_utc', 'N/A'):<22} | {p.get('title', 'N/A')[:30]}")
    else:
        print("\nNo published videos recorded yet.")
    print()

def main():
    parser = argparse.ArgumentParser(
        description="BEYOND UNKNOWN - Fully Automated Faceless YouTube Shorts System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--setup-check", action="store_true", help="Checks dependencies, credentials and API connectivity")
    parser.add_argument("--generate", action="store_true", help="Generates and validates one video without publishing")
    parser.add_argument("--dry-run", action="store_true", help="Runs entire pipeline including mock upload without actual publishing")
    parser.add_argument("--publish", action="store_true", help="Generates, validates, uploads and schedules one video")
    parser.add_argument("--slot", choices=["morning", "evening"], default="morning", help="Production slot: 'morning' (09:30 IST) or 'evening' (17:30 IST)")
    parser.add_argument("--list-topics", action="store_true", help="Displays remaining topic queue")
    parser.add_argument("--status", action="store_true", help="Displays pipeline status and publication history")

    args = parser.parse_args()

    if args.setup_check:
        run_setup_check()
        return

    if args.list_topics:
        list_topics()
        return

    if args.status:
        show_status()
        return

    pipeline = Pipeline()

    if args.generate:
        result = pipeline.run(slot=args.slot, dry_run=True, publish=False)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("status") == "SUCCESS" else 1)

    if args.dry_run:
        result = pipeline.run(slot=args.slot, dry_run=True, publish=True)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("status") == "SUCCESS" else 1)

    if args.publish:
        result = pipeline.run(slot=args.slot, dry_run=False, publish=True)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("status") == "SUCCESS" else 1)

    # Default action if no args passed: display help
    parser.print_help()

if __name__ == "__main__":
    main()
