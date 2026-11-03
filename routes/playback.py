"""
routes/playback.py

Player page and HLS file serving with smart seek support.
"""

import os
import time
import logging
import urllib.parse

from flask import Blueprint, render_template, abort, send_from_directory

import config
from media.filesystem import safe_join
from transcoding.manager import manager, JobState

logger = logging.getLogger(__name__)

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

    # Add to recent files
    from routes.favorites import add_to_recent
    add_to_recent(path)

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
    Serve HLS files from the cache directory with smart segment handling.

    For .ts segment files:
        If the segment doesn't exist yet (user seeked ahead):
          1. Check if current transcode will reach it soon → wait
          2. If far away → kill current transcode, restart at seek position
        
        This enables instant seeking anywhere in the timeline:
          - Browser requests segment N
          - This route checks if FFmpeg is heading there
          - If not, restarts FFmpeg at position N
          - Waits for segment to be created
          - Serves the segment

    For .m3u8 and .vtt files:
        Served immediately — no waiting.
    """
    # Prevent path traversal inside video_id itself
    if "/" in video_id or "\\" in video_id or ".." in video_id:
        abort(403)

    directory = os.path.join(config.HLS_CACHE_DIR, video_id)

    if not os.path.isdir(directory):
        abort(404)
    
    file_path = os.path.join(directory, filename)

    # For .ts segment files, implement smart waiting/restart logic
    if filename.endswith(".ts") and not os.path.exists(file_path):
        # Extract segment number from filename (seg_NNN.ts)
        try:
            # Handle both video/seg_NNN.ts and audio_N/seg_NNN.ts
            seg_name = os.path.basename(filename)
            if seg_name.startswith("seg_") and seg_name.endswith(".ts"):
                requested_segment = int(seg_name[4:7])  # seg_NNN.ts
            else:
                # Not a standard segment file, return 404
                abort(404)
        except (ValueError, IndexError):
            abort(404)
        
        # Get the transcode job
        from transcoding.manager import manager
        job_status = manager.get_status(video_id)
        
        if not job_status:
            abort(404)
        
        # Get the job object to check current position
        with manager._registry_lock:
            job = manager._registry.get(video_id)
        
        if not job:
            abort(404)
        
        # Decide: wait or restart?
        if job.should_wait_for_segment(requested_segment):
            # Segment is close, wait for it
            logger.info(
                "Segment %d requested, current position %d, waiting: %s",
                requested_segment, job.current_segment, video_id
            )
            
            waited   = 0.0
            interval = 0.25

            while waited < config.SEGMENT_WAIT_TIMEOUT:
                time.sleep(interval)
                waited += interval

                if os.path.exists(file_path):
                    break
                
                # Check if transcode failed while we were waiting
                if job.state == JobState.FAILED:
                    abort(500)
            else:
                # Timeout — segment never appeared
                logger.warning(
                    "Timeout waiting for segment %d: %s",
                    requested_segment, video_id
                )
                abort(404)
        else:
            # Segment is far away, restart FFmpeg at this position
            start_time = requested_segment * config.HLS_SEGMENT_TIME
            logger.info(
                "Segment %d requested, current position %d, restarting at %.1fs: %s",
                requested_segment, job.current_segment, start_time, video_id
            )
            
            # Restart transcode at new position
            manager._restart_at_position(job, start_time)
            
            # Wait for the segment to be created
            waited   = 0.0
            interval = 0.25

            while waited < config.HLS_READY_TIMEOUT:
                time.sleep(interval)
                waited += interval

                if os.path.exists(file_path):
                    break
                
                # Check if transcode failed
                if job.state == JobState.FAILED:
                    abort(500)
            else:
                # Timeout
                logger.error(
                    "Timeout waiting for segment %d after restart: %s",
                    requested_segment, video_id
                )
                abort(404)

    return send_from_directory(directory, filename)

