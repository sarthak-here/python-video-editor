"""
Core video processing logic using MoviePy.
All heavy lifting happens here — main.py just calls these functions.
"""

import os
from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
)
from moviepy.audio.fx.all import volumex


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _out(filename: str) -> str:
    return os.path.join(OUTPUT_DIR, filename)


# ── Trim ────────────────────────────────────────────────────────────────────

def trim_video(input_path: str, start: float, end: float, output_name: str) -> str:
    """Cut a clip from start to end (seconds)."""
    clip = VideoFileClip(input_path)
    duration = clip.duration

    start = max(0.0, min(start, duration))
    end   = max(start + 0.1, min(end, duration))

    trimmed = clip.subclip(start, end)
    out = _out(output_name)
    trimmed.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return out


# ── Merge ────────────────────────────────────────────────────────────────────

def merge_videos(input_paths: list[str], output_name: str) -> str:
    """Concatenate a list of video files in order."""
    clips = [VideoFileClip(p) for p in input_paths]
    final = concatenate_videoclips(clips, method="compose")
    out = _out(output_name)
    final.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    for c in clips:
        c.close()
    return out


# ── Text overlay ─────────────────────────────────────────────────────────────

def add_text(
    input_path: str,
    text: str,
    output_name: str,
    font_size: int = 50,
    color: str = "white",
    position: str = "bottom",   # "top" | "center" | "bottom"
    start: float = 0.0,
    end: float | None = None,
) -> str:
    """Burn a text overlay onto the video."""
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


# ── Audio control ─────────────────────────────────────────────────────────────

def adjust_audio(
    input_path: str,
    output_name: str,
    volume: float = 1.0,   # 0.0 = mute, 1.0 = original, 2.0 = double
    replace_audio_path: str | None = None,
) -> str:
    """Mute, boost, or replace audio in a video."""
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
