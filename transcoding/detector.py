"""
transcoding/detector.py

FFprobe wrapper.  Analyses a media file and returns a MediaInfo object.
Results are cached to cache/metadata/<hash>.json and reused as long as
the source file has not been modified (mtime-based invalidation).
"""

import os
import json
import logging
import subprocess
import hashlib
from typing import Optional

import config
from media.models import MediaInfo

logger = logging.getLogger(__name__)


# ============================================================
# PUBLIC API
# ============================================================

def get_media_info(file_path: str) -> MediaInfo:
    """
    Return MediaInfo for file_path.
    Uses cached ffprobe output when fresh; runs ffprobe otherwise.

    Raises RuntimeError if ffprobe is missing or the file is unreadable.
    """
    os.makedirs(config.METADATA_CACHE_DIR, exist_ok=True)

    cache_path = _cache_path(file_path)

    if _cache_valid(file_path, cache_path):
        raw = _load_cache(cache_path)
        if raw is not None:
            logger.debug("Metadata cache hit: %s", os.path.basename(file_path))
            return _parse(file_path, raw)

    logger.info("Probing: %s", os.path.basename(file_path))
    raw = _run_ffprobe(file_path)

    _save_cache(cache_path, raw)

    return _parse(file_path, raw)


# ============================================================
# FFPROBE
# ============================================================

def _run_ffprobe(file_path: str) -> dict:
    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not found. Install it with: pkg install ffmpeg"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobe timed out on: {file_path}")

    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (code {result.returncode}): "
            f"{result.stderr.strip()}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe produced invalid JSON: {exc}") from exc


# ============================================================
# CACHE HELPERS
# ============================================================

def _cache_path(file_path: str) -> str:
    key = hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.METADATA_CACHE_DIR, f"{key}.json")


def _cache_valid(file_path: str, cache_path: str) -> bool:
    if not os.path.exists(cache_path):
        return False
    try:
        return os.path.getmtime(cache_path) >= os.path.getmtime(file_path)
    except OSError:
        return False


def _load_cache(cache_path: str) -> Optional[dict]:
    try:
        with open(cache_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _save_cache(cache_path: str, raw: dict) -> None:
    try:
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh)
    except OSError as exc:
        logger.warning("Could not write metadata cache: %s", exc)


# ============================================================
# PARSING
# ============================================================

def _parse(file_path: str, raw: dict) -> MediaInfo:
    streams = raw.get("streams", [])
    fmt     = raw.get("format", {})

    video_stream:  Optional[dict] = None
    audio_streams: int            = 0
    first_audio:   Optional[dict] = None
    has_subtitles: bool           = False

    for s in streams:
        ctype = s.get("codec_type")
        if ctype == "video" and video_stream is None:
            video_stream = s
        elif ctype == "audio":
            audio_streams += 1
            if first_audio is None:
                first_audio = s
        elif ctype == "subtitle":
            has_subtitles = True

    # Video
    video_codec   = None
    video_width   = None
    video_height  = None
    video_fps     = None
    pixel_format  = None

    if video_stream:
        video_codec  = video_stream.get("codec_name")
        video_width  = video_stream.get("width")
        video_height = video_stream.get("height")
        pixel_format = video_stream.get("pix_fmt")

        fps_str = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            video_fps = round(int(num) / int(den), 3) if int(den) else None
        except (ValueError, ZeroDivisionError):
            video_fps = None

    # Audio
    audio_codec = first_audio.get("codec_name") if first_audio else None

    # Container / duration / bitrate
    container = fmt.get("format_name", "unknown")

    duration: Optional[float] = None
    try:
        duration = float(fmt.get("duration", 0)) or None
    except (ValueError, TypeError):
        pass

    bitrate: Optional[int] = None
    try:
        bitrate = int(fmt.get("bit_rate", 0)) or None
    except (ValueError, TypeError):
        pass

    return MediaInfo(
        path=file_path,
        container=container,
        duration=duration,
        video_codec=video_codec,
        video_width=video_width,
        video_height=video_height,
        video_fps=video_fps,
        pixel_format=pixel_format,
        audio_codec=audio_codec,
        audio_streams=audio_streams,
        bitrate=bitrate,
        has_subtitles=has_subtitles,
        raw=raw,
    )
