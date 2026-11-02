"""
routes/playback.py

Player page and HLS file serving.
"""

import os
import time
import urllib.parse

from flask import Blueprint, render_template, abort, send_from_directory

import config
from media.filesystem import safe_join
from transcoding.manager import manager

playback_bp = Blueprint("playback", __name__)


# ============================================================
# PLAYER PAGE
# ============================================================

@playback_bp.route("/player/<path:path>")
def player(path: str):
    source = safe_join(config.MEDIA_ROOT, path)

    if not os.path.isfile(source):
        abort(404)

    _, ext = os.path.splitext(source)
    if ext.lower() not in config.VIDEO_EXTENSIONS:
        abort(400)

    # Submit the job (non-blocking — returns instantly)
    job = manager.submit(relative_path=path, source_path=source)

    # Back link
    parent_path = os.path.dirname(path)
    back = (
        "/browse/" + urllib.parse.quote(parent_path, safe="/")
        if parent_path
        else "/browse/"
    )

    return render_template(
        "player.html",
        name=os.path.basename(source),
        video_id=job.video_id,
        back=back,
    )


# ============================================================
# HLS FILE SERVING
# ============================================================

@playback_bp.route("/hls/<video_id>/<path:filename>")
def hls_file(video_id: str, filename: str):
    """
    Serve HLS files from the cache directory.

    For .ts segment files:
        If the segment has not yet been created by FFmpeg (the user seeked
        ahead of the current transcode position), hold the HTTP connection
        open and poll until FFmpeg creates the file or the timeout expires.

        This is what makes full-timeline seeking work:
          1. The browser loads stream.m3u8 (pre-generated VOD playlist
             covering the entire video duration).
          2. The user can drag the seek bar anywhere immediately.
          3. The browser requests the segment at the seek position.
          4. This route waits until FFmpeg reaches that segment.
          5. The segment is served; playback resumes.

    For .m3u8 and .vtt files:
        Served immediately — no waiting.
    """
    # Prevent path traversal inside video_id itself
    if "/" in video_id or "\\" in video_id or ".." in video_id:
        abort(403)

    directory = os.path.join(config.HLS_CACHE_DIR, video_id)

    if not os.path.isdir(directory):
        abort(404)

    # For .ts segment files, wait if not yet transcoded
    if filename.endswith(".ts"):
        file_path = os.path.join(directory, filename)

        if not os.path.exists(file_path):
            waited   = 0.0
            interval = 0.25

            while waited < config.SEGMENT_WAIT_TIMEOUT:
                time.sleep(interval)
                waited += interval

                if os.path.exists(file_path):
                    break
            else:
                # Segment never appeared — FFmpeg may have failed
                abort(404)

    return send_from_directory(directory, filename)

