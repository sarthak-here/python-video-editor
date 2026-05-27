# 🎬 Python Video Editor

A browser-based video editor built with **FastAPI** + **MoviePy** + **FFmpeg**.

## Features

| Feature | Description |
|---|---|
| ✂️ **Trim** | Cut a video between any two timestamps |
| 🔗 **Merge** | Concatenate multiple video files in order |
| 🔤 **Add Text** | Burn text overlays with custom font, color & position |
| 🔊 **Audio** | Mute, boost volume, or replace the entire audio track |

### 🎞️ Frame-by-Frame Preview (Trim & Add Text)

When you pick a video file in the **Trim** or **Add Text** tabs, an inline preview panel appears instantly — no extra upload needed.

| Control | Action |
|---|---|
| **← / → arrow keys** | Step one frame backward / forward |
| **Space** | Play / Pause |
| **i** | Mark In at current frame |
| **o** | Mark Out at current frame |
| **⬅ Mark In** button | Set the In point — auto-fills the *Start* field |
| **Mark Out ➡** button | Set the Out point — auto-fills the *End* field |
| Click / drag timeline | Seek to any position |
| FPS selector | Switch between 24 / 25 / 30 / 60 fps for accurate stepping |
| 🔊 / 🔇 toggle | Mute or unmute preview audio |

The selected range is highlighted on the timeline, and both timestamps flash in the form fields when set so you always know they've been applied.

## Requirements
- Python 3.10+
- FFmpeg installed and on PATH

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/sarthak-here/python-video-editor.git
cd python-video-editor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn main:app --reload
```

Then open **http://localhost:8000** in your browser.

## Project Structure
```
video-editor/
├── main.py              # FastAPI routes
├── editor.py            # MoviePy processing logic
├── templates/
│   └── index.html       # Browser UI
├── static/
│   ├── style.css        # All styles including preview panel
│   └── app.js           # Tab logic, VideoPreview class, form handling
├── uploads/             # Temp input files (gitignored)
├── outputs/             # Processed videos (gitignored)
└── requirements.txt
```

## Stack
- **Backend** — FastAPI, MoviePy, FFmpeg
- **Frontend** — Vanilla HTML/CSS/JS (no framework)
