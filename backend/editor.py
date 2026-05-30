"""
Core video processing logic using MoviePy.
All heavy lifting happens here — main.py just calls these functions.
"""

import os
import numpy as np
from PIL import Image, ImageEnhance
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


# ── Color / Transform adjustments ────────────────────────────────────────────

_SEPIA = np.array([
    [0.393, 0.769, 0.189],
    [0.349, 0.686, 0.168],
    [0.272, 0.534, 0.131],
], dtype=np.float32)


def _apply_hue_shift(frame: np.ndarray, shift_deg: float) -> np.ndarray:
    """Shift hue of an H×W×3 uint8 frame. Returns uint8."""
    f = frame.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]

    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    diff = maxc - minc
    safe = np.where(diff > 1e-7, diff, 1.0)

    rc = (maxc - r) / safe
    gc = (maxc - g) / safe
    bc = (maxc - b) / safe

    h = np.select(
        [diff < 1e-7, r == maxc, g == maxc],
        [0.0, (bc - gc) / 6.0, (2.0 + rc - bc) / 6.0],
        default=(4.0 + gc - rc) / 6.0,
    )
    h = (h % 1.0 + shift_deg / 360.0) % 1.0

    v = maxc
    s = np.where(maxc > 1e-7, diff / maxc, 0.0)

    i   = (h * 6).astype(np.int32)
    ff  = h * 6 - i
    p   = v * (1.0 - s)
    q   = v * (1.0 - s * ff)
    t   = v * (1.0 - s * (1.0 - ff))
    i6  = i % 6

    out = np.zeros_like(f)
    for ci, (rv, gv, bv) in enumerate([(v, t, p), (q, v, p), (p, v, t),
                                        (p, q, v), (t, p, v), (v, p, q)]):
        mask = (i6 == ci)[..., np.newaxis]
        out = np.where(mask, np.stack([rv, gv, bv], axis=-1), out)

    return np.clip(out * 255, 0, 255).astype(np.uint8)


def _make_adjuster(clip_w, clip_h, brightness, contrast, saturation, sharpness,
                   gamma, hue_shift, grayscale, sepia, invert, vignette):
    """Return a frame-processing function for clip.fl_image(...)."""
    vign_mask = None
    if vignette > 0.0:
        Y, X = np.ogrid[:clip_h, :clip_w]
        dist_norm = np.sqrt(
            ((X - clip_w / 2) / (clip_w / 2)) ** 2 +
            ((Y - clip_h / 2) / (clip_h / 2)) ** 2
        ) / np.sqrt(2)
        vign_mask = np.clip(1.0 - vignette * dist_norm ** 2, 0.0, 1.0
                            )[..., np.newaxis].astype(np.float32)

    needs_pil = (brightness != 1.0 or contrast != 1.0 or
                 saturation != 1.0 or sharpness != 1.0)

    def process(frame):
        if needs_pil:
            img = Image.fromarray(frame)
            if brightness != 1.0:
                img = ImageEnhance.Brightness(img).enhance(brightness)
            if contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(contrast)
            if saturation != 1.0:
                img = ImageEnhance.Color(img).enhance(saturation)
            if sharpness != 1.0:
                img = ImageEnhance.Sharpness(img).enhance(sharpness)
            frame = np.array(img, dtype=np.uint8)

        if hue_shift != 0.0:
            frame = _apply_hue_shift(frame, hue_shift)

        f = frame.astype(np.float32)

        if gamma != 1.0:
            f = np.power(np.clip(f / 255.0, 0.0, 1.0), 1.0 / gamma) * 255.0

        if grayscale:
            gray = f[..., 0] * 0.2989 + f[..., 1] * 0.5870 + f[..., 2] * 0.1140
            f = np.stack([gray, gray, gray], axis=-1)
        elif sepia:
            f = np.clip(f @ _SEPIA.T, 0.0, 255.0)

        if invert:
            f = 255.0 - f

        if vign_mask is not None:
            f = f * vign_mask

        return np.clip(f, 0, 255).astype(np.uint8)

    return process


def adjust_video(
    input_path: str,
    output_name: str,
    brightness: float = 1.0,
    contrast:   float = 1.0,
    saturation: float = 1.0,
    sharpness:  float = 1.0,
    gamma:      float = 1.0,
    hue_shift:  float = 0.0,
    grayscale:  bool  = False,
    sepia:      bool  = False,
    invert:     bool  = False,
    vignette:   float = 0.0,
    speed:      float = 1.0,
    flip_h:     bool  = False,
    flip_v:     bool  = False,
    rotate_deg: float = 0.0,
) -> str:
    from moviepy.video.fx.all import speedx, mirror_x, mirror_y
    from moviepy.video.fx.all import rotate as mpy_rotate

    clip = VideoFileClip(input_path)
    w, h = clip.size

    needs_frame = (
        brightness != 1.0 or contrast != 1.0 or saturation != 1.0 or
        sharpness != 1.0 or gamma != 1.0 or hue_shift != 0.0 or
        grayscale or sepia or invert or vignette > 0.0
    )
    if needs_frame:
        fn = _make_adjuster(w, h, brightness, contrast, saturation, sharpness,
                            gamma, hue_shift, grayscale, sepia, invert, vignette)
        clip = clip.fl_image(fn)

    if speed != 1.0:
        clip = clip.fx(speedx, speed)
    if flip_h:
        clip = clip.fx(mirror_x)
    if flip_v:
        clip = clip.fx(mirror_y)
    if rotate_deg != 0.0:
        clip = clip.fx(mpy_rotate, rotate_deg)

    out = _out(output_name)
    clip.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return out
