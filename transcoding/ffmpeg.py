"""
transcoding/ffmpeg.py

FFmpeg subprocess helpers — Phase 5 (multi-audio).

Changes from Phase 1:
  - build_transcode_command() REMOVED.
  - build_video_command() — video-only HLS (no audio).
  - build_audio_command() — single audio track HLS (no video).
  - launch() and check_available() unchanged.
"""

import os
import logging
import subprocess
from typing import Tuple

import config
from media.models import MediaInfo

logger = logging.getLogger(__name__)


# ============================================================
# VIDEO COMMAND
# ============================================================

def build_video_command(
    source: str,
    output_dir: str,
    media_info: MediaInfo,
    start_time: float = 0.0,
    start_segment: int = 0,
) -> list:
    """
    Build FFmpeg command for video-only HLS with optional seek support.
    
    Args:
        source: Path to source video file
        output_dir: Base output directory
        media_info: Metadata from ffprobe
        start_time: Seek to this timestamp (seconds) before transcoding
        start_segment: Segment number to start with (start_time / HLS_SEGMENT_TIME)
    
    Output goes to <output_dir>/video/stream.m3u8.
    No audio is included — audio is in separate playlists.
    
    When start_time > 0, FFmpeg:
      - Seeks to start_time BEFORE reading (fast)
      - Forces exact keyframes every 6s so segment math works
      - Numbers segments starting from start_segment
      - Offsets timestamps so the browser's timeline stays correct
    """
    video_dir = os.path.join(output_dir, "video")
    playlist  = os.path.join(video_dir, "ffmpeg.m3u8")   # internal; not served to browser
    seg_tmpl  = os.path.join(video_dir, "seg_%03d.ts")

    cmd = ["ffmpeg", "-y"]
    
    # SEEK BEFORE INPUT (instant seek, doesn't decode from 0)
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    
    cmd.extend(["-i", source])

    # First video stream only
    cmd.extend(["-map", "0:v:0"])

    # Ensure even dimensions (libx264 requirement) - keeps original resolution
    cmd.extend(["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"])

    # Universal H.264 - Optimized for 1080p mobile real-time encoding
    cmd.extend([
        "-c:v",       config.VIDEO_CODEC,
        "-preset",    config.VIDEO_PRESET,
        "-crf",       str(config.VIDEO_CRF),
        "-profile:v", "high",
        "-level",     "4.1",
        "-pix_fmt",   "yuv420p",
        "-threads",   "0",             # auto (let FFmpeg decide)
        "-tune",      "zerolatency",   # optimize for real-time streaming
        "-g",         str(config.HLS_SEGMENT_TIME * 25),  # GOP size = fps * segment (fewer keyframes)
        "-x264-params", "nal-hrd=cbr:force-cfr=1:ref=2:bframes=0",  # CBR, 2 ref frames, no B-frames for speed
    ])
    
    # FORCE EXACT KEYFRAMES every HLS_SEGMENT_TIME seconds
    # This ensures segment N always means "time N × segment_time"
    # Without this, segments drift with natural keyframe positions
    if start_time > 0:
        cmd.extend([
            "-force_key_frames",
            f"expr:gte(t,n_forced*{config.HLS_SEGMENT_TIME})"
        ])

    # No audio in video stream
    cmd.extend(["-an"])

    # HLS output
    cmd.extend([
        "-f",                    "hls",
        "-hls_time",             str(config.HLS_SEGMENT_TIME),
        "-hls_playlist_type",    "event",
        "-hls_segment_type",     "mpegts",
        "-hls_flags",            "independent_segments",
        "-hls_segment_filename", seg_tmpl,
    ])
    
    # SEGMENT NUMBERING for resume/seek
    if start_segment > 0:
        cmd.extend(["-start_number", str(start_segment)])
        cmd.extend(["-output_ts_offset", str(start_time)])

    cmd.append(playlist)

    return cmd


# ============================================================
# AUDIO COMMAND
# ============================================================

def build_audio_command(
    source: str,
    output_dir: str,
    track_index: int,
    start_time: float = 0.0,
    start_segment: int = 0,
) -> list:
    """
    Build FFmpeg command for a single audio track HLS with optional seek support.
    
    Args:
        source: Path to source video file
        output_dir: Base output directory
        track_index: Which audio track to extract (0-indexed among audio streams)
        start_time: Seek to this timestamp (seconds) before transcoding
        start_segment: Segment number to start with
    
    Output goes to <output_dir>/audio_<N>/stream.m3u8.
    No video is included.
    """
    audio_dir = os.path.join(output_dir, f"audio_{track_index}")
    playlist  = os.path.join(audio_dir, "ffmpeg.m3u8")   # internal; not served to browser
    seg_tmpl  = os.path.join(audio_dir, "seg_%03d.ts")

    cmd = ["ffmpeg", "-y"]
    
    # SEEK BEFORE INPUT
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    
    cmd.extend(["-i", source])

    # The Nth audio stream
    cmd.extend(["-map", f"0:a:{track_index}"])

    # AAC stereo
    cmd.extend([
        "-c:a",  config.AUDIO_CODEC,
        "-b:a",  config.AUDIO_BITRATE,
        "-ac",   config.AUDIO_CHANNELS,
        "-ar",   config.AUDIO_SAMPLE_RATE,
    ])

    # No video
    cmd.extend(["-vn"])

    # HLS output
    cmd.extend([
        "-f",                    "hls",
        "-hls_time",             str(config.HLS_SEGMENT_TIME),
        "-hls_playlist_type",    "event",
        "-hls_segment_type",     "mpegts",
        "-hls_flags",            "independent_segments",
        "-hls_segment_filename", seg_tmpl,
    ])
    
    # SEGMENT NUMBERING for resume/seek
    if start_segment > 0:
        cmd.extend(["-start_number", str(start_segment)])
        cmd.extend(["-output_ts_offset", str(start_time)])

    cmd.append(playlist)

    return cmd


# ============================================================
# SUBTITLE COMMAND
# ============================================================

def build_subtitle_command(
    source: str,
    output_dir: str,
    track_index: int,
) -> list:
    """
    Build FFmpeg command to extract one subtitle track to WebVTT.

    Output: <output_dir>/sub_<N>.vtt  (single file, not segmented)

    Only call this for text-based subtitle codecs.
    Image-based codecs (PGS, VOBSUB) cannot be converted to WebVTT
    and must be filtered out before calling this function.
    """
    vtt_path = os.path.join(output_dir, f"sub_{track_index}.vtt")

    return [
        "ffmpeg",
        "-y",
        "-i", source,
        "-map",  f"0:s:{track_index}",
        "-c:s",  "webvtt",
        vtt_path,
    ]


# ============================================================
# LAUNCH
# ============================================================

def launch(command: list, log_path: str) -> subprocess.Popen:
    """
    Start FFmpeg as a detached background process.
    stdout is discarded; stderr is written to log_path.
    Never uses shell=True.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger.info("FFmpeg starting — log: %s", log_path)
    logger.debug("FFmpeg command: %s", " ".join(command))

    # Open log file and let subprocess inherit it, then close Python's handle
    with open(log_path, "w", encoding="utf-8", errors="replace") as log_fh:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=log_fh,
            close_fds=True,
        )
    # log_fh is closed here, but subprocess still has the FD
    return proc


# ============================================================
# AVAILABILITY CHECK
# ============================================================

def check_available() -> Tuple[bool, bool]:
    """Check whether ffmpeg and ffprobe are on PATH."""
    def _probe(cmd: str) -> bool:
        try:
            subprocess.run(
                [cmd, "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    return _probe("ffmpeg"), _probe("ffprobe")
