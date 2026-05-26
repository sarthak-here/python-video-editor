# 🎬 Python Video Editor

A browser-based video editor built with **FastAPI** + **MoviePy** + **FFmpeg**.

## Features
| Feature | Description |
|---|---|
| ✂️ **Trim** | Cut a video between any two timestamps |
| 🔗 **Merge** | Concatenate multiple video files in order |
| 🔤 **Add Text** | Burn text overlays with custom font, color & position |
| 🔊 **Audio** | Mute, boost volume, or replace the entire audio track |

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
│   ├── style.css
│   └── app.js
├── uploads/             # Temp input files (gitignored)
├── outputs/             # Processed videos (gitignored)
└── requirements.txt
```

## Stack
- **Backend** — FastAPI, MoviePy, FFmpeg
- **Frontend** — Vanilla HTML/CSS/JS (no framework needed)
