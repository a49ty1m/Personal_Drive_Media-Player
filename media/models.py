from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MediaFile:
    """A single video file discovered in MEDIA_ROOT."""
    name: str            # bare filename, e.g. "Movie.mkv"
    relative: str        # path relative to MEDIA_ROOT, forward-slash separated
    extension: str       # lowercase extension, e.g. ".mkv"


@dataclass
class Folder:
    """A directory discovered under MEDIA_ROOT."""
    name: str            # bare directory name
    relative: str        # path relative to MEDIA_ROOT, forward-slash separated


@dataclass
class MediaInfo:
    """Result of ffprobe analysis for a single media file."""
    path: str

    # Container
    container: str                   # e.g. "matroska,webm"
    duration: Optional[float]        # total duration in seconds

    # Video stream (first video track)
    video_codec: Optional[str]       # e.g. "hevc", "h264"
    video_width: Optional[int]
    video_height: Optional[int]
    video_fps: Optional[float]
    pixel_format: Optional[str]      # e.g. "yuv420p", "yuv420p10le"

    # Audio
    audio_codec: Optional[str]       # codec of the first audio stream
    audio_streams: int               # total number of audio streams

    # Other
    bitrate: Optional[int]           # overall bitrate in bps
    has_subtitles: bool

    # Raw ffprobe output for future use
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class PlaybackDecision:
    """Result of the playback strategy decision."""
    mode: str     # "transcode" | "direct"
    reason: str   # human-readable explanation


@dataclass
class JobStatus:
    """Current state of a transcoding job."""
    video_id: str
    state: str              # "pending" | "transcoding" | "ready" | "failed"
    message: str            # human-readable status
    hls_url: Optional[str] = None
    error: Optional[str]   = None
    audio_tracks: List[dict] = field(default_factory=list)
    subtitle_tracks: List[dict] = field(default_factory=list)
