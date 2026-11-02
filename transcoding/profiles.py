"""
transcoding/profiles.py

Playback decision logic: should this file be direct-played or transcoded?

Phase 1: Always transcode to H.264/AAC HLS.
Phase 2 will add direct-play detection based on codec + container.
"""

import logging
from media.models import MediaInfo, PlaybackDecision

logger = logging.getLogger(__name__)


def decide_playback(media_info: MediaInfo) -> PlaybackDecision:
    """
    Determine whether to direct-play or transcode the given media.

    Phase 1 strategy: always transcode.

    This ensures maximum browser compatibility regardless of source codec
    (HEVC, AV1, 10-bit, unusual containers, etc.).

    Phase 2 will add logic such as:
        if media_info.video_codec == "h264"
           and media_info.audio_codec in ("aac", "mp3")
           and media_info.container in ("mp4", "mov,mp4,m4a,...")
           and media_info.pixel_format == "yuv420p":
            return PlaybackDecision("direct", "H.264/AAC MP4 — direct play")
    """
    reason = (
        f"Phase 1 universal transcode "
        f"[video={media_info.video_codec or 'unknown'}, "
        f"audio={media_info.audio_codec or 'unknown'}, "
        f"container={media_info.container}]"
    )

    logger.info("Playback decision: TRANSCODE — %s", reason)

    return PlaybackDecision(mode="transcode", reason=reason)
