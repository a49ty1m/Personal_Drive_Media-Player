"""
transcoding/manager.py — Phase 5 + subtitle support

New in this version:
  - Text-based subtitle streams (SRT, ASS, SSA, WebVTT, mov_text …)
    are extracted to <output_dir>/sub_<N>.vtt in parallel with audio.
  - Image-based subtitle codecs (PGS, VOBSUB, DVBSUB) are skipped
    gracefully with a log message.
  - subtitle_tracks list persisted to subtitle_tracks.json (same
    pattern as audio_tracks.json) for zero-cost cache hits.
  - Subtitle processes do NOT block the READY state — extraction is
    nearly instantaneous and completes well before first playback.
"""

import os
import json
import math
import time
import shutil
import hashlib
import logging
import threading
from enum import Enum
from typing import List, Optional

import config
from media.models import MediaInfo, JobStatus
import transcoding.ffmpeg as ffmpeg_module
from transcoding.detector import get_media_info

logger = logging.getLogger(__name__)

# ============================================================
# LANGUAGE MAP  (ISO 639-1 and ISO 639-2 → display name)
# ============================================================
_LANG_NAMES = {
    "eng": "English",    "en":  "English",
    "hin": "Hindi",      "hi":  "Hindi",
    "tam": "Tamil",      "ta":  "Tamil",
    "tel": "Telugu",     "te":  "Telugu",
    "mal": "Malayalam",  "ml":  "Malayalam",
    "kan": "Kannada",    "kn":  "Kannada",
    "mar": "Marathi",    "mr":  "Marathi",
    "ben": "Bengali",    "bn":  "Bengali",
    "pan": "Punjabi",    "pa":  "Punjabi",
    "guj": "Gujarati",   "gu":  "Gujarati",
    "ori": "Odia",       "or":  "Odia",
    "urd": "Urdu",       "ur":  "Urdu",
    "ara": "Arabic",     "ar":  "Arabic",
    "jpn": "Japanese",   "ja":  "Japanese",
    "zho": "Chinese",    "chi": "Chinese",  "zh": "Chinese",
    "fra": "French",     "fr":  "French",
    "deu": "German",     "ger": "German",   "de": "German",
    "spa": "Spanish",    "es":  "Spanish",
    "por": "Portuguese", "pt":  "Portuguese",
    "rus": "Russian",    "ru":  "Russian",
    "kor": "Korean",     "ko":  "Korean",
    "ita": "Italian",    "it":  "Italian",
    "tha": "Thai",       "th":  "Thai",
    "vie": "Vietnamese", "vi":  "Vietnamese",
}

# ============================================================
# SUBTITLE CODEC FILTER
# ============================================================
# Only these codecs can be converted to WebVTT by FFmpeg.
# Image-based codecs (hdmv_pgs_subtitle, dvd_subtitle, dvbsub …)
# are excluded — they require burn-in which is out of scope.
_TEXT_SUBTITLE_CODECS = frozenset({
    "subrip", "srt", "ass", "ssa", "webvtt", "mov_text", "text",
    "microdvd", "subviewer", "subviewer1", "jacosub", "realtext",
    "sami", "stl", "pjs", "mpl2",
})


# ============================================================
# HELPERS
# ============================================================

def _track_name(tags: dict, lang: str, fallback: str) -> str:
    """Resolve a human-readable track name from ffprobe tag metadata."""
    title = tags.get("title", "").strip()
    return (
        _LANG_NAMES.get(lang)
        or (title if title else None)
        or (lang.upper() if lang not in ("und", "") else None)
        or fallback
    )


def _extract_audio_tracks(streams: list) -> List[dict]:
    tracks = []
    idx = 0
    for s in streams:
        if s.get("codec_type") != "audio":
            continue
        tags = s.get("tags", {})
        lang = tags.get("language", "und").lower().strip()
        tracks.append({
            "index":    idx,
            "name":     _track_name(tags, lang, f"Audio {idx + 1}"),
            "language": lang,
        })
        idx += 1
    return tracks


def _extract_subtitle_tracks(streams: list) -> List[dict]:
    """
    Return subtitle tracks that can be converted to WebVTT.
    Image-based codecs are skipped with a log entry.
    """
    tracks = []
    sub_idx  = 0   # index among ALL subtitle streams (used in -map 0:s:<N>)
    kept_idx = 0   # index among KEPT tracks (used for sub_<N>.vtt filenames)

    for s in streams:
        if s.get("codec_type") != "subtitle":
            continue

        codec = s.get("codec_name", "").lower()
        tags  = s.get("tags", {})
        lang  = tags.get("language", "und").lower().strip()

        if codec not in _TEXT_SUBTITLE_CODECS:
            logger.info(
                "Skipping image-based subtitle stream %d (%s) — "
                "cannot convert to WebVTT",
                sub_idx, codec,
            )
            sub_idx += 1
            continue

        tracks.append({
            "index":       kept_idx,     # position among kept tracks
            "source_index": sub_idx,      # actual -map 0:s:<N> index
            "name":        _track_name(tags, lang, f"Subtitle {kept_idx + 1}"),
            "language":    lang,
            "codec":       codec,
        })
        sub_idx  += 1
        kept_idx += 1

    return tracks


def _write_vod_playlist(playlist_path: str, duration: float) -> int:
    """
    Pre-generate a complete HLS VOD playlist for the full video duration.

    Uses #EXT-X-PLAYLIST-TYPE:VOD and #EXT-X-ENDLIST so the browser
    immediately knows the full timeline length and can render a complete
    seek bar.  Each segment entry uses the configured HLS_SEGMENT_TIME
    except the last segment which carries the remainder.

    FFmpeg writes its own internal playlist (ffmpeg.m3u8) alongside
    these files.  The browser always reads stream.m3u8 (this file).

    Returns the number of segments.
    """
    seg_time = config.HLS_SEGMENT_TIME

    num_segs = max(1, math.ceil(duration / seg_time))

    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        f"#EXT-X-TARGETDURATION:{seg_time}",
        "#EXT-X-PLAYLIST-TYPE:VOD",
        "",
    ]

    for i in range(num_segs):
        if i < num_segs - 1:
            seg_dur = float(seg_time)
        else:
            seg_dur = duration - (num_segs - 1) * seg_time
            if seg_dur <= 0.001:
                seg_dur = float(seg_time)
        lines.append(f"#EXTINF:{seg_dur:.3f},")
        lines.append(f"seg_{i:03d}.ts")

    lines.append("#EXT-X-ENDLIST")
    lines.append("")

    with open(playlist_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    logger.info(
        "VOD playlist: %d segments, %.1fs — %s",
        num_segs, duration, os.path.basename(playlist_path),
    )
    return num_segs


def _write_master(master_path: str, audio_tracks: List[dict]) -> None:
    """Write the HLS master playlist (video + audio renditions)."""
    lines = ["#EXTM3U", "#EXT-X-VERSION:3", ""]

    if audio_tracks:
        for i, track in enumerate(audio_tracks):
            default = "YES" if i == 0 else "NO"
            lines.append(
                '#EXT-X-MEDIA:TYPE=AUDIO,'
                'GROUP-ID="audio",'
                f'NAME="{track["name"]}",'
                f'LANGUAGE="{track["language"]}",'
                f'DEFAULT={default},'
                'AUTOSELECT=YES,'
                f'URI="audio_{i}/stream.m3u8"'
            )
        lines.append("")
        lines.append(
            '#EXT-X-STREAM-INF:BANDWIDTH=5000000,'
            'CODECS="avc1.640028",'
            'AUDIO="audio"'
        )
    else:
        lines.append('#EXT-X-STREAM-INF:BANDWIDTH=5000000,CODECS="avc1.640028"')

    lines.append("video/stream.m3u8")
    lines.append("")

    with open(master_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    logger.info("master.m3u8 written: %s",
                os.path.basename(os.path.dirname(master_path)))


def _log_tail(log_path: str, lines: int = 25) -> str:
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            return "\n".join(fh.read().strip().splitlines()[-lines:])
    except OSError:
        return "(log not available)"


# ============================================================
# JOB
# ============================================================

class JobState(Enum):
    PENDING     = "pending"
    TRANSCODING = "transcoding"
    READY       = "ready"
    FAILED      = "failed"


class TranscodeJob:
    def __init__(self, video_id: str, source_path: str):
        self.video_id    = video_id
        self.source_path = source_path
        self.output_dir  = os.path.join(config.HLS_CACHE_DIR, video_id)

        # Key paths
        self.master           = os.path.join(self.output_dir, "master.m3u8")
        self.audio_tracks_file = os.path.join(self.output_dir, "audio_tracks.json")
        self.sub_tracks_file  = os.path.join(self.output_dir, "subtitle_tracks.json")
        self.video_first_seg  = os.path.join(self.output_dir, "video", "seg_000.ts")
        self.audio_first_seg  = os.path.join(self.output_dir, "audio_0", "seg_000.ts")

        # Track metadata (write-once before READY; read-only after)
        self.audio_tracks:    List[dict] = []
        self.subtitle_tracks: List[dict] = []

        # All running Popen objects
        self.processes: list = []

        # Thread-safe state
        self._lock    = threading.Lock()
        self._state   = JobState.PENDING
        self._message = "Queued"
        self._error: Optional[str] = None

    @property
    def state(self) -> JobState:
        with self._lock:
            return self._state

    @property
    def message(self) -> str:
        with self._lock:
            return self._message

    @property
    def error(self) -> Optional[str]:
        with self._lock:
            return self._error

    def set_state(
        self,
        state: JobState,
        message: str,
        error: Optional[str] = None,
    ) -> None:
        with self._lock:
            self._state   = state
            self._message = message
            self._error   = error


# ============================================================
# MANAGER
# ============================================================

class TranscodeManager:
    def __init__(self):
        self._registry: dict[str, TranscodeJob] = {}
        self._registry_lock = threading.Lock()
        self._semaphore = threading.Semaphore(config.MAX_TRANSCODES)

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def get_video_id(self, relative_path: str) -> str:
        return hashlib.sha256(
            relative_path.encode("utf-8")
        ).hexdigest()[:16]

    def submit(self, relative_path: str, source_path: str) -> TranscodeJob:
        video_id = self.get_video_id(relative_path)

        with self._registry_lock:
            if video_id in self._registry:
                return self._registry[video_id]
            job = TranscodeJob(video_id=video_id, source_path=source_path)
            self._registry[video_id] = job

        if self._cache_valid(job):
            job.audio_tracks    = self._load_json(job.audio_tracks_file)
            job.subtitle_tracks = self._load_json(job.sub_tracks_file)
            job.set_state(JobState.READY, "Cached — ready to play")
            logger.info("Cache hit: %s", video_id)
            return job

        self._wipe_cache(job)

        t = threading.Thread(
            target=self._run,
            args=(job,),
            daemon=True,
            name=f"transcode-{video_id}",
        )
        t.start()

        return job

    def get_status(self, video_id: str) -> Optional[JobStatus]:
        with self._registry_lock:
            job = self._registry.get(video_id)

        if job is None:
            return None

        hls_url = (
            f"/hls/{job.video_id}/master.m3u8"
            if job.state == JobState.READY
            else None
        )

        return JobStatus(
            video_id=video_id,
            state=job.state.value,
            message=job.message,
            hls_url=hls_url,
            error=job.error,
            audio_tracks=job.audio_tracks,
            subtitle_tracks=job.subtitle_tracks,
        )

    # ----------------------------------------------------------
    # Cache helpers
    # ----------------------------------------------------------

    def _cache_valid(self, job: TranscodeJob) -> bool:
        if not os.path.exists(job.master):
            return False
        if not os.path.exists(job.video_first_seg):
            return False
        try:
            return (
                os.path.getmtime(job.master)
                >= os.path.getmtime(job.source_path)
            )
        except OSError:
            return False

    def _wipe_cache(self, job: TranscodeJob) -> None:
        if os.path.exists(job.output_dir):
            try:
                shutil.rmtree(job.output_dir)
            except OSError as exc:
                logger.warning("Could not wipe cache: %s", exc)

    def _load_json(self, path: str) -> list:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return []

    def _save_json(self, path: str, data: list) -> None:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except OSError as exc:
            logger.warning("Could not write %s: %s", os.path.basename(path), exc)

    # ----------------------------------------------------------
    # Background transcoding
    # ----------------------------------------------------------

    def _run(self, job: TranscodeJob) -> None:
        job.set_state(JobState.PENDING, "Waiting for a transcoding slot\u2026")
        self._semaphore.acquire()
        try:
            self._transcode(job)
        finally:
            self._semaphore.release()

    def _transcode(self, job: TranscodeJob) -> None:
        try:
            os.makedirs(job.output_dir, exist_ok=True)

            # ---- Probe ----
            job.set_state(JobState.TRANSCODING, "Analysing media\u2026")

            try:
                media_info: MediaInfo = get_media_info(job.source_path)
            except RuntimeError as exc:
                raise RuntimeError(f"ffprobe failed: {exc}") from exc

            if not media_info.video_codec:
                raise RuntimeError("Source file contains no video stream.")

            streams = media_info.raw.get("streams", [])

            # ---- Extract track metadata ----
            audio_tracks    = _extract_audio_tracks(streams)
            subtitle_tracks = _extract_subtitle_tracks(streams)

            job.audio_tracks    = audio_tracks
            job.subtitle_tracks = subtitle_tracks

            self._save_json(job.audio_tracks_file, audio_tracks)
            self._save_json(job.sub_tracks_file, subtitle_tracks)

            logger.info(
                "Codec: video=%s  audio=%s streams=%d  subtitles=%d (text-based)",
                media_info.video_codec,
                media_info.audio_codec,
                media_info.audio_streams,
                len(subtitle_tracks),
            )

            # ---- Create output subdirectories ----
            os.makedirs(os.path.join(job.output_dir, "video"), exist_ok=True)
            for i in range(len(audio_tracks)):
                os.makedirs(os.path.join(job.output_dir, f"audio_{i}"), exist_ok=True)
            # No subdirectory needed for .vtt files — they go in output_dir directly

            # ---- Write pre-generated VOD playlists (full seekable timeline) ----
            # Written BEFORE FFmpeg starts so the browser immediately has the
            # complete seek bar.  Segment files are created by FFmpeg on demand;
            # the route blocks requests for not-yet-created segments.
            if media_info.duration:
                _write_vod_playlist(
                    os.path.join(job.output_dir, "video", "stream.m3u8"),
                    media_info.duration,
                )
                for i in range(len(audio_tracks)):
                    _write_vod_playlist(
                        os.path.join(job.output_dir, f"audio_{i}", "stream.m3u8"),
                        media_info.duration,
                    )
            else:
                logger.warning(
                    "Duration unknown — seek bar will be limited to "
                    "transcoded portion: %s",
                    job.video_id,
                )

            # ---- Build status message ----
            parts = ["Transcoding video"]
            if audio_tracks:
                parts.append(f"{len(audio_tracks)} audio track"
                             + ("s" if len(audio_tracks) > 1 else ""))
            if subtitle_tracks:
                parts.append(f"{len(subtitle_tracks)} subtitle track"
                             + ("s" if len(subtitle_tracks) > 1 else ""))
            job.set_state(JobState.TRANSCODING, " + ".join(parts) + "\u2026")

            # ---- Launch video FFmpeg ----
            video_cmd = ffmpeg_module.build_video_command(
                source=job.source_path,
                output_dir=job.output_dir,
                media_info=media_info,
            )
            video_log = os.path.join(config.LOG_DIR, f"{job.video_id}_video.log")
            video_proc = ffmpeg_module.launch(video_cmd, video_log)
            logger.info("Video FFmpeg PID %d: %s", video_proc.pid, job.video_id)

            # ---- Launch audio FFmpeg processes (parallel) ----
            audio_procs = []
            for i in range(len(audio_tracks)):
                cmd = ffmpeg_module.build_audio_command(
                    source=job.source_path,
                    output_dir=job.output_dir,
                    track_index=i,
                )
                log = os.path.join(config.LOG_DIR, f"{job.video_id}_audio_{i}.log")
                proc = ffmpeg_module.launch(cmd, log)
                audio_procs.append(proc)
                logger.info(
                    "Audio FFmpeg PID %d (track %d: %s): %s",
                    proc.pid, i, audio_tracks[i]["name"], job.video_id,
                )

            # ---- Launch subtitle FFmpeg processes (parallel, non-blocking) ----
            # These finish in seconds; we don't wait for them before READY.
            sub_procs = []
            for track in subtitle_tracks:
                cmd = ffmpeg_module.build_subtitle_command(
                    source=job.source_path,
                    output_dir=job.output_dir,
                    track_index=track["source_index"],
                )
                log = os.path.join(
                    config.LOG_DIR,
                    f"{job.video_id}_sub_{track['index']}.log"
                )
                proc = ffmpeg_module.launch(cmd, log)
                sub_procs.append(proc)
                logger.info(
                    "Subtitle FFmpeg PID %d (track %d: %s [%s]): %s",
                    proc.pid, track["index"], track["name"],
                    track["codec"], job.video_id,
                )

            job.processes = [video_proc] + audio_procs + sub_procs

            # ---- Wait for first video segment ----
            waited = 0.0
            while waited < config.HLS_READY_TIMEOUT:
                ret = video_proc.poll()
                if ret is not None and ret != 0:
                    raise RuntimeError(
                        f"Video FFmpeg exited with code {ret}.\n"
                        f"{_log_tail(video_log)}"
                    )
                if os.path.exists(job.video_first_seg):
                    break
                if ret == 0 and os.path.exists(job.video_first_seg):
                    break
                time.sleep(config.HLS_POLL_INTERVAL)
                waited += config.HLS_POLL_INTERVAL
            else:
                self._kill_all(job.processes)
                raise RuntimeError(
                    f"Timeout waiting for first video segment "
                    f"({config.HLS_READY_TIMEOUT}s). Log: {video_log}"
                )

            # ---- Wait for first audio segment (if audio exists) ----
            if audio_procs:
                waited = 0.0
                audio_log_0 = os.path.join(
                    config.LOG_DIR, f"{job.video_id}_audio_0.log"
                )
                while waited < config.HLS_READY_TIMEOUT:
                    if os.path.exists(job.audio_first_seg):
                        break
                    ret = audio_procs[0].poll()
                    if ret is not None and ret != 0:
                        raise RuntimeError(
                            f"Audio FFmpeg (track 0) exited with code {ret}.\n"
                            f"{_log_tail(audio_log_0)}"
                        )
                    time.sleep(config.HLS_POLL_INTERVAL)
                    waited += config.HLS_POLL_INTERVAL
                else:
                    self._kill_all(job.processes)
                    raise RuntimeError("Timeout waiting for first audio segment.")

            # ---- Write master playlist ----
            _write_master(job.master, audio_tracks)

            # ---- Browser can start playing ----
            job.set_state(JobState.READY, "Ready")
            logger.info("HLS ready: %s", job.video_id)

            # ---- Wait for all processes (remaining segments + subtitle extraction) ----
            video_proc.wait()
            for proc in audio_procs + sub_procs:
                proc.wait()

            # Log any subtitle failures (non-fatal at this point)
            for i, proc in enumerate(sub_procs):
                if proc.returncode != 0:
                    logger.warning(
                        "Subtitle extraction failed for track %d "
                        "(code %d) — subtitle may not be available: %s",
                        subtitle_tracks[i]["index"],
                        proc.returncode,
                        job.video_id,
                    )

            logger.info("Transcoding complete: %s", job.video_id)

        except Exception as exc:
            logger.error("Transcode failed [%s]: %s", job.video_id, exc)
            job.set_state(JobState.FAILED, "Transcoding failed", error=str(exc))
            with self._registry_lock:
                self._registry.pop(job.video_id, None)

    @staticmethod
    def _kill_all(processes: list) -> None:
        for proc in processes:
            try:
                proc.kill()
            except OSError:
                pass


# ============================================================
# GLOBAL SINGLETON
# ============================================================

manager = TranscodeManager()
