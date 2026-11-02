"""
routes/api.py

JSON API for client-side polling.
"""

from flask import Blueprint, jsonify

from transcoding.manager import manager

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/status/<video_id>")
def job_status(video_id: str):
    """
    Return current transcoding status for a video_id.

    Response schema:
    {
        "status":  "pending" | "transcoding" | "ready" | "failed",
        "message": "<human-readable string>",
        "hls_url": "/hls/<id>/stream.m3u8" | null,
        "error":   "<error string>" | null
    }
    """
    status = manager.get_status(video_id)

    if status is None:
        return jsonify({
            "status":  "unknown",
            "message": "Job not found. Try reloading the page.",
            "hls_url": None,
            "error":   None,
        }), 404

    return jsonify({
        "status":          status.state,
        "message":         status.message,
        "hls_url":         status.hls_url,
        "error":           status.error,
        "audio_tracks":    status.audio_tracks,
        "subtitle_tracks": status.subtitle_tracks,
    })
