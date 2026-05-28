"""
Python Video Editor — single-file entry point.
Run with: uvicorn app:app --reload
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip,
)
from moviepy.audio.fx.all import volumex


# ── Directories ──────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="Python Video Editor")
app.mount("/static",  StaticFiles(directory=BASE_DIR / "static"),  name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR),           name="outputs")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR),           name="uploads")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ── Video processing ─────────────────────────────────────────────────────────

def _out(filename: str) -> str:
    return str(OUTPUT_DIR / filename)


def trim_video(input_path: str, start: float, end: float, output_name: str) -> str:
    clip = VideoFileClip(input_path)
    duration = clip.duration
    start = max(0.0, min(start, duration))
    end   = max(start + 0.1, min(end, duration))
    trimmed = clip.subclip(start, end)
    out = _out(output_name)
    trimmed.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return out


def merge_videos(input_paths: list[str], output_name: str) -> str:
    clips = [VideoFileClip(p) for p in input_paths]
    final = concatenate_videoclips(clips, method="compose")
    out = _out(output_name)
    final.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    for c in clips:
        c.close()
    return out


def add_text(
    input_path: str,
    text: str,
    output_name: str,
    font_size: int = 50,
    color: str = "white",
    position: str = "bottom",
    start: float = 0.0,
    end: float | None = None,
) -> str:
    clip = VideoFileClip(input_path)
    end = end or clip.duration
    pos_map = {
        "top":    ("center", 30),
        "center": ("center", "center"),
        "bottom": ("center", clip.size[1] - 80),
    }
    xy_pos = pos_map.get(position, ("center", "center"))
    txt = (
        TextClip(text, fontsize=font_size, color=color, font="Arial")
        .set_position(xy_pos)
        .set_start(start)
        .set_end(end)
    )
    composite = CompositeVideoClip([clip, txt])
    out = _out(output_name)
    composite.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return out


def adjust_audio(
    input_path: str,
    output_name: str,
    volume: float = 1.0,
    replace_audio_path: str | None = None,
) -> str:
    clip = VideoFileClip(input_path)
    if replace_audio_path:
        from moviepy.editor import AudioFileClip
        new_audio = AudioFileClip(replace_audio_path).subclip(0, clip.duration)
        clip = clip.set_audio(new_audio)
    elif volume == 0.0:
        clip = clip.without_audio()
    else:
        clip = clip.fx(volumex, volume)
    out = _out(output_name)
    clip.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return out


# ── Helpers ──────────────────────────────────────────────────────────────────

def save_upload(file: UploadFile) -> str:
    ext  = Path(file.filename).suffix
    name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return str(dest)

def unique_output(suffix: str = ".mp4") -> str:
    return f"{uuid.uuid4().hex}{suffix}"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/trim")
async def trim(
    file:  UploadFile = File(...),
    start: float      = Form(0.0),
    end:   float      = Form(10.0),
):
    path = save_upload(file)
    try:
        out = trim_video(path, start, end, unique_output())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"url": f"/outputs/{Path(out).name}", "filename": Path(out).name}


@app.post("/merge")
async def merge(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 videos to merge.")
    paths = [save_upload(f) for f in files]
    try:
        out = merge_videos(paths, unique_output())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"url": f"/outputs/{Path(out).name}", "filename": Path(out).name}


@app.post("/add-text")
async def add_text_route(
    file:      UploadFile = File(...),
    text:      str        = Form(...),
    font_size: int        = Form(50),
    color:     str        = Form("white"),
    position:  str        = Form("bottom"),
    start:     float      = Form(0.0),
    end:       float      = Form(0.0),
):
    path = save_upload(file)
    end_val = end if end > 0 else None
    try:
        out = add_text(path, text, unique_output(),
                       font_size=font_size, color=color,
                       position=position, start=start, end=end_val)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"url": f"/outputs/{Path(out).name}", "filename": Path(out).name}


@app.post("/audio")
async def audio_control(
    file:          UploadFile           = File(...),
    volume:        float                = Form(1.0),
    replace_audio: Optional[UploadFile] = File(None),
):
    path = save_upload(file)
    audio_path = save_upload(replace_audio) if replace_audio and replace_audio.filename else None
    try:
        out = adjust_audio(path, unique_output(), volume=volume,
                           replace_audio_path=audio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"url": f"/outputs/{Path(out).name}", "filename": Path(out).name}


@app.get("/download/{filename}")
async def download(filename: str):
    fp = OUTPUT_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(fp), media_type="video/mp4",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
