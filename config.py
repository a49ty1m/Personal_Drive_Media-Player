"""
config.py — All configuration for the Termux Media Server.

Override any value with an environment variable of the same name:

    MEDIA_ROOT=/storage/downloads python app.py
    PORT=9090 python app.py
"""

import os

# ============================================================
# MEDIA
# ============================================================

# Root directory containing all movies and TV series.
#
# Default: the PARENT folder of the media-server directory.
# Layout:  web_sharing_folder/
#              media-server/   ← this app lives here
#              Movie.mkv       ← served from here
#              TV Show/        ← served from here
#
# Override: MEDIA_ROOT=/path/to/folder python app.py
_APP_DIR   = os.path.dirname(os.path.abspath(__file__))   # .../media-server
_SHARE_DIR = os.path.dirname(_APP_DIR)                    # .../web_sharing_folder

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", _SHARE_DIR)


# Supported video file extensions (lowercase).
VIDEO_EXTENSIONS = {
    ".mkv", ".mp4", ".webm", ".m4v",
    ".mov", ".avi", ".ts"
}

# All file extensions to display in browser (None = show all files).
# When None, shows all file types; when set to a set, only shows those extensions.
BROWSEABLE_EXTENSIONS = None  # Show all files

# Common file type categories for icons
FILE_CATEGORIES = {
    "video": {".mkv", ".mp4", ".webm", ".m4v", ".mov", ".avi", ".ts", ".flv", ".wmv"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"},
    "document": {".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf"},
    "spreadsheet": {".xls", ".xlsx", ".csv", ".ods"},
    "presentation": {".ppt", ".pptx", ".odp"},
    "archive": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "code": {".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".sh", ".json", ".xml", ".yml", ".yaml"},
}

# ============================================================
# NETWORK
# ============================================================

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

# ============================================================
# FILE UPLOAD & DELETION
# ============================================================

# Enable file upload functionality
UPLOAD_ENABLED = os.environ.get("UPLOAD_ENABLED", "true").lower() == "true"

# Maximum upload file size (in bytes)
# Default: 500 MB
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", str(500 * 1024 * 1024)))

# Enable file/folder deletion functionality
DELETE_ENABLED = os.environ.get("DELETE_ENABLED", "true").lower() == "true"

# Maximum folder size for ZIP download (in bytes)
# Default: 1 GB (above this, ZIP creation is not possible on Termux)
# Set to 0 to disable size limit
MAX_ZIP_SIZE = int(os.environ.get("MAX_ZIP_SIZE", str(1024 * 1024 * 1024)))

# Optional: Password protection for uploads (None = disabled)
# Set via: UPLOAD_PASSWORD=mysecret python app.py
UPLOAD_PASSWORD = os.environ.get("UPLOAD_PASSWORD", None)

# Optional: Password protection for deletions (None = disabled)
DELETE_PASSWORD = os.environ.get("DELETE_PASSWORD", None)

# Allowed file extensions for upload (None = allow all)
ALLOWED_UPLOAD_EXTENSIONS = None  # Allow all file types

# ============================================================
# TRANSCODING
# ============================================================

# Maximum simultaneous FFmpeg processes.
# Keep at 1 on Android — phones cannot handle multiple 1080p
# transcodes simultaneously.
MAX_TRANSCODES = int(os.environ.get("MAX_TRANSCODES", "1"))

# HLS segment duration in seconds.
HLS_SEGMENT_TIME = int(os.environ.get("HLS_SEGMENT_TIME", "10"))  # longer segments = less CPU load

# Video encoding - Optimized for mobile playback
VIDEO_CODEC   = "libx264"
VIDEO_PRESET  = "veryfast"    # faster encoding, much lighter on CPU
VIDEO_CRF     = 30            # lower quality but smooth playback (23=high, 30=medium)

# Audio encoding - simplified for mobile
AUDIO_CODEC       = "aac"
AUDIO_BITRATE     = "96k"      # reduced from 128k (enough for mobile speakers)
AUDIO_SAMPLE_RATE = "44100"    # standard quality
AUDIO_CHANNELS    = "2"        # stereo

# Timeout (seconds) waiting for the first HLS segment to appear.
HLS_READY_TIMEOUT = int(os.environ.get("HLS_READY_TIMEOUT", "120"))

# Polling interval (seconds) while waiting for first segment.
HLS_POLL_INTERVAL = 0.25

# When the browser requests a segment that doesn't exist yet,
# how long (seconds) to hold the HTTP request open waiting for FFmpeg
# to create it.  If the segment doesn't appear within this timeout,
# the current transcode job is killed and restarted at the requested position.
SEGMENT_WAIT_TIMEOUT = int(os.environ.get("SEGMENT_WAIT_TIMEOUT", "30"))

# Maximum total cache size in bytes (default: 500 MB for mobile).
# When cache exceeds this limit after a transcode completes, the least
# recently accessed video folders are deleted until under the cap.
# Set to 0 to disable automatic cleanup.
MAX_CACHE_SIZE = int(os.environ.get("MAX_CACHE_SIZE", str(500 * 1024 * 1024)))

# ============================================================
# PATHS
# ============================================================

import tempfile as _tempfile

# Base directory for all server-generated files.
# Uses the system temp dir (works on Linux, Android/Termux, macOS).
#   Linux:  /tmp/media-server
#   Termux: /data/data/com.termux/files/usr/tmp/media-server
# Override: SERVER_DIR=/sdcard/media-cache python app.py
_SERVER_DIR = os.environ.get(
    "SERVER_DIR",
    os.path.join(_tempfile.gettempdir(), "media-server")
)


# Cache: transcoded HLS output and ffprobe metadata.
CACHE_DIR          = os.path.join(_SERVER_DIR, "cache")
HLS_CACHE_DIR      = os.path.join(CACHE_DIR, "hls")
METADATA_CACHE_DIR = os.path.join(CACHE_DIR, "metadata")

# FFmpeg stderr logs per job.
LOG_DIR = os.path.join(_SERVER_DIR, "logs")

# hls.js — must be placed at this path before running.
# See README.md for the download command.
HLS_JS_PATH = os.path.join(_APP_DIR, "static", "js", "hls.min.js")

# ============================================================
# FLASK
# ============================================================

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
