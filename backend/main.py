import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import editor

ROOT_DIR    = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
UPLOAD_DIR  = BACKEND_DIR / "uploads"
OUTPUT_DIR  = BACKEND_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Python Video Editor")
app.mount("/static",  StaticFiles(directory=ROOT_DIR / "frontend" / "static"),  name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=str(ROOT_DIR / "frontend" / "templates"))


def save_upload(file: UploadFile) -> str:
    ext  = Path(file.filename).suffix
    name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return str(dest)

def unique_output(suffix: str = ".mp4") -> str:
    return f"{uuid.uuid4().hex}{suffix}"


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
        out = editor.trim_video(path, start, end, unique_output())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"url": f"/outputs/{Path(out).name}", "filename": Path(out).name}


@app.post("/merge")
async def merge(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 videos to merge.")
    paths = [save_upload(f) for f in files]
    try:
        out = editor.merge_videos(paths, unique_output())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"url": f"/outputs/{Path(out).name}", "filename": Path(out).name}


@app.post("/add-text")
async def add_text(
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
        out = editor.add_text(path, text, unique_output(),
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
        out = editor.adjust_audio(path, unique_output(), volume=volume,
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
