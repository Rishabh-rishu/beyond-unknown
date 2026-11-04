# BEYOND UNKNOWN – FULLY AUTOMATED YOUTUBE SHORTS SYSTEM

> **Channel Name:** BEYOND UNKNOWN  
> **Tagline:** DISCOVER WHAT THE WORLD HIDES.  
> **Format:** Vertical 9:16 (1080x1920) YouTube Shorts  
> **Language:** Hinglish (Natural Hindi + English documentary mix)  
> **Frequency:** Exactly 2 Unique Shorts Daily (09:30 AM & 05:30 PM India Time)  
> **Voice Speed:** Exactly 1.15x (pitch-preserved narration)  

---

## 🌟 Overview

**Beyond Unknown** is a fully automated, production-grade AI documentary generation and publishing pipeline. Built for high-retention storytelling, it produces factually grounded, cinematographically composed YouTube Shorts without requiring manual scriptwriting, voice recording, editing, or uploading.

The system is configured to run automatically through **GitHub Actions** twice every day:
1. **Morning Slot (09:30 AM IST):** Focuses on Hidden India, ancient Indian architecture, forgotten technology, and Indian geography.
2. **Evening Slot (05:30 PM IST):** Focuses on global mysteries, strange nature, cutting-edge science, and space exploration.

---

## 🎨 Visual Design & Branding Identity

Every Short adheres to a strict cinematic documentary standard:
- **Color Palette:**
  - `Midnight Black (#10151E)` – Deep documentary contrast
  - `Deep Navy (#182638)` – Card backgrounds & atmospheric depth
  - `Antique Gold (#D6B56D)` – Keyword accents, borders & badges
  - `Warm White (#F5F1E8)` – High-legibility narration typography
- **Typography:**
  - `Cinzel` – Monumental headings and fact panels
  - `Montserrat` – Secondary statistics, badges, and captions
  - `Noto Sans Devanagari` – Flawless Hindi unicode rendering
- **Mobile Safe Areas:**
  - Top margin: `240 px` (avoids YouTube channel overlay & search)
  - Bottom margin: `380 px` (avoids audio icon, title bar & subscribe buttons)
  - Left margin: `80 px`, Right margin: `140 px` (avoids like/share stack)
- **Topic-Adaptive Layouts:**
  - `archaeological_card`: Ancient stone framing with antique gold corner brackets.
  - `telemetry_hud`: Deep-space coordinate grids and orbital reticles.
  - `stat_card`: High-contrast documentary statistic panels.
  - `clean_documentary`: Minimalist vignette layout.

---

## 🗂️ System Architecture

```text
beyond-unknown/
├── .github/
│   └── workflows/
│       └── daily_shorts.yml       # Production cron scheduler & manual dispatch
├── config/
│   ├── settings.py                # Global environment & path management
│   ├── brand.json                 # Branding guidelines, safe zones & palette
│   └── music_config.json          # 6 Mood categories & CC0 licensing info
├── data/
│   ├── topics.json                # 180 curated unique topics (first 90 days)
│   ├── published_tracker.json     # Permanent publication ledger & YouTube IDs
│   ├── rejected_topics.json       # Audit log of rejected topics
│   └── research_cache.json        # Cached multi-source research dossiers
├── research/
│   ├── researcher.py              # Multi-source research orchestrator
│   ├── source_validator.py        # Domain authority & HTTPS verification
│   └── fact_checker.py            # Filters conspiracy tropes & validates claims
├── ai/
│   ├── gemini_client.py           # Google Gemini API client with retries & fallback
│   ├── topic_generator.py         # Multi-tier deduplication & queue replenishment
│   └── script_generator.py        # Hinglish scriptwriting & visual scene planner
├── assets/
│   ├── pexels_client.py           # Priority 1: Vertical cinematic video & photo
│   ├── wikimedia_client.py        # Priority 2: CC historical & archaeological media
│   ├── nasa_client.py             # Priority 3: NASA public domain planetary imagery
│   ├── procedural_graphics.py     # Priority 4: 1080x1920 layout card compositor
│   ├── asset_manager.py           # Multi-provider asset coordinator
│   ├── fonts/                     # Bundled Cinzel, Montserrat & Devanagari fonts
│   └── audio/                     # 6 High-quality CC0 ambient master tracks
├── voice/
│   ├── tts_engine.py              # Edge TTS engine with word-boundary extraction
│   └── audio_processor.py         # FFmpeg atempo=1.15 speedup & loudness normalization
├── video/
│   ├── scene_planner.py           # Audio-synchronized scene cut calculator
│   ├── subtitle_generator.py      # Mobile-safe ASS subtitles with Antique Gold highlight
│   ├── music_selector.py          # Category-based ambient score selector
│   ├── video_editor.py            # Complete FFmpeg production assembly & export
│   └── quality_checker.py         # 10-Point pre-upload verification & blackdetect
├── youtube/
│   ├── auth.py                    # OAuth2 token manager & desktop auth flow
│   ├── scheduler.py               # Dynamic IST -> UTC RFC 3339 publishing calculator
│   └── uploader.py                # Resumable video upload & thumbnail publisher
├── automation/
│   ├── state_manager.py           # Checkpoint manager for run states
│   ├── recovery.py                # Failure recovery & resume logic
│   └── pipeline.py                # End-to-end master orchestrator
├── output/
│   ├── videos/                    # Generated 1080x1920 MP4 Shorts
│   ├── audio/                     # Processed 1.15x narration audio
│   └── scripts/                   # Structured script metadata
├── tests/                         # Comprehensive unit & integration test suite
├── main.py                        # CLI entry point
├── requirements.txt               # Locked production dependencies
├── pytest.ini                     # Test configuration
├── .env.example                   # Environment configuration template
└── README.md                      # Complete system documentation
```

---

## ⚙️ Installation & Setup Guide

### 1. Install Python 3.12+
On Ubuntu / Debian:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```
On macOS:
```bash
brew install python
```

### 2. Install FFmpeg 6.0+
FFmpeg is required for audio speedup, video composition, and subtitle burning:
```bash
sudo apt install -y ffmpeg
# Verify installation:
ffmpeg -version
ffprobe -version
```

### 3. Clone and Setup Virtual Environment
```bash
git clone https://github.com/your-username/beyond-unknown.git
cd beyond-unknown

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 API Keys & Credentials Configuration

Copy the example environment template:
```bash
cp .env.example .env
```

### 1. Google Gemini API (Required)
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and generate a new key.
3. Add to `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_FALLBACK_MODEL=gemini-1.5-flash
   ```

### 2. Pexels API (Optional but Recommended)
1. Create a free account at [Pexels Developer Portal](https://www.pexels.com/api/).
2. Generate an API Key.
3. Add to `.env`:
   ```env
   PEXELS_API_KEY=your_pexels_key_here
   ```
   *Note: If no Pexels key is provided, the system seamlessly falls back to Wikimedia Commons, NASA, and the custom Procedural Graphics Engine.*

### 3. YouTube Data API v3 & OAuth Setup (Required for Publishing)
To schedule private videos through the YouTube API:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `Beyond-Unknown-Automation`).
3. Navigate to **APIs & Services** > **Library**, search for **YouTube Data API v3**, and click **Enable**.
4. Go to **APIs & Services** > **OAuth consent screen**:
   - Choose **External**.
   - Fill in App Name: `Beyond Unknown Automation`.
   - Add your own Google Account as a **Test User**.
5. Go to **APIs & Services** > **Credentials**:
   - Click **Create Credentials** > **OAuth client ID**.
   - Select Application type: **Desktop App**.
   - Name it `YouTube Shorts Publisher`.
   - Download the client secrets file as `client_secrets.json`.
6. Run the local authentication helper to generate your refresh token:
   ```bash
   python -c "from youtube.auth import YouTubeAuth; YouTubeAuth.run_local_oauth_flow('client_secrets.json')"
   ```
   A browser window will open. Sign in with your YouTube channel account and grant upload permissions.
7. The terminal will print your credentials. Copy them to `.env`:
   ```env
   YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=your_client_secret
   YOUTUBE_REFRESH_TOKEN=1//04...
   ```

---

## 🚀 Command-Line Interface (CLI)

The system includes a CLI for verification, manual runs, and queue inspection:

```bash
# 1. Verify all dependencies, fonts, audio, and credentials
python main.py --setup-check

# 2. Inspect remaining topics in the queue (out of 180 initial topics)
python main.py --list-topics

# 3. View pipeline status and recent upload records
python main.py --status

# 4. Generate and validate one morning video without uploading (Dry-Run)
python main.py --dry-run --slot morning

# 5. Generate and validate one evening video without uploading (Dry-Run)
python main.py --dry-run --slot evening

# 6. Generate, validate, and publish/schedule the morning Short (09:30 AM IST)
python main.py --publish --slot morning

# 7. Generate, validate, and publish/schedule the evening Short (05:30 PM IST)
python main.py --publish --slot evening
```

---

## 🤖 GitHub Actions Daily Automation Setup

The repository is pre-configured with `.github/workflows/daily_shorts.yml` to produce two original Shorts daily on schedule:
- **Morning Run:** Triggers at **08:15 AM IST** (`cron: '45 2 * * *'`) for publication at **09:30 AM IST**.
- **Evening Run:** Triggers at **04:15 PM IST** (`cron: '45 10 * * *'`) for publication at **05:30 PM IST**.

### Setting Up GitHub Repository Secrets
1. Push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initialize Beyond Unknown Production System"
   git branch -M main
   git remote add origin https://github.com/your-username/beyond-unknown.git
   git push -u origin main
   ```
2. In your GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Under **Repository secrets**, click **New repository secret** and add:
   - `GEMINI_API_KEY`: Your Google AI Studio API key.
   - `GEMINI_MODEL`: `gemini-2.5-flash` (or your preferred model).
   - `GEMINI_FALLBACK_MODEL`: `gemini-1.5-flash`.
   - `PEXELS_API_KEY`: Your Pexels API key (optional).
   - `YOUTUBE_CLIENT_ID`: Your Google OAuth Client ID.
   - `YOUTUBE_CLIENT_SECRET`: Your Google OAuth Client Secret.
   - `YOUTUBE_REFRESH_TOKEN`: Your YouTube OAuth Refresh Token.
4. Go to **Settings** > **Actions** > **General** > **Workflow permissions**:
   - Select **Read and write permissions** (allows the workflow to commit updated topic publication trackers).
   - Click **Save**.

### Triggering a Test Run in GitHub Actions
1. Go to the **Actions** tab in GitHub.
2. Select **Daily Automated YouTube Shorts (Beyond Unknown)**.
3. Click **Run workflow**:
   - Choose `dry-run` to test the full pipeline safely without publishing.
   - Or choose `morning` / `evening` to schedule an actual Short.

---

## 🕒 How to Change Publishing Times

To change publishing times, adjust these two locations:

1. **In `.env` or settings:**
   ```env
   MORNING_PUBLISH_TIME=10:00
   EVENING_PUBLISH_TIME=18:00
   ```
2. **In `.github/workflows/daily_shorts.yml`:**
   Convert your desired workflow trigger time (1h 15m before publish) to UTC:
   - Example for 10:00 AM IST: Workflow at 08:45 AM IST = `45 3 * * *` UTC.
   - Example for 06:00 PM IST: Workflow at 04:45 PM IST = `45 11 * * *` UTC.

---

## 🧪 Testing & Verification

Run the comprehensive unit and integration test suite:
```bash
pytest tests/ -v
```

The test suite validates:
- Multi-tier topic deduplication and slot filtering.
- Domain authority verification and Wikipedia-only rejection.
- Pseudoscientific conspiracy filtering and fact verification.
- Pydantic schema parsing for Hinglish scripts and scene items.
- Exact `1.15x` voice speedup and timestamp scaling.
- ASS subtitle generation and Antique Gold keyword highlighting.
- IST to UTC dynamic scheduling conversion and date rollovers.
- YouTube upload metadata formatting and dry-run simulation.
- Checkpoint persistence and failure recovery.
- End-to-end dry-run pipeline execution and fail-safe publishing policies.

---

## 🛡️ License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
All bundled ambient background audio tracks are released under **Creative Commons CC0 1.0 Universal / Public Domain**.
