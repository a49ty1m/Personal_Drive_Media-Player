# Termux Media Server

A lightweight, modular local media server that runs natively inside
**Termux on Android**. No proot, no Debian, no Docker, no systemd.

Stream your movies and TV series from your phone to any browser on
the same Wi-Fi network.

---

## Features (Phase 1)

- Browse movies and TV series in any nested folder structure
- Universal transcoding to H.264/AAC HLS via FFmpeg
- Non-blocking player: page loads immediately, stream starts as soon
  as the first segment is ready
- Automatic cache: transcoded videos are reused on subsequent plays
- mtime-based cache invalidation: replacing a file auto-retranscodes
- Path traversal protection — media root is the only exposed directory
- Configurable via environment variables, no config file editing needed
- Zero external Python dependencies beyond Flask

## 🆕 Personal Drive Features

Transform your media server into a full personal cloud drive:

### File Management
- **Upload** - Drag & drop multiple files, support ALL file types, 500MB limit
- **Download** - Direct download with 3-dot menu or from preview
- **Delete** - Files and folders with confirmation dialog
- **Create Folders** - Easy folder creation with name validation
- **File Preview** - Click filename to preview images, text, PDFs (with zoom!), audio

### PDF Viewer
- Zoom controls: 🔍+ (zoom in), 🔍− (zoom out), ⟲ (reset)
- Zoom range: 50% to 300% in 25% steps
- Live zoom percentage display
- Smooth transitions
- Zoom controls only for PDFs (not for images)

### User Interface
- Dark-themed preview modal
- 3-dot menu (⋮) for clean actions (download/delete)
- File type icons (🎬 videos, 📄 documents, 🖼️ images, 🎵 audio)
- File sizes displayed (KB, MB, GB)
- Row layout for folders and files
- Responsive design for desktop and mobile
- Clean button layout (Download left of Close button)

### How to Use
1. **Browse**: Navigate folders as usual
2. **Create Folder**: Click "📁 Create Folder" → enter name → press Enter or Create
3. **Upload**: Click "📤 Upload Files" → drag & drop or browse → Upload
4. **Preview**: Click on any filename to preview (images, text, PDFs, audio)
5. **Download**: Click 3-dot menu (⋮) → Download, or Download button in preview
6. **Delete**: Click 3-dot menu (⋮) → Delete → Confirm
7. **PDF Zoom**: In PDF preview, use 🔍+ to zoom in, 🔍− to zoom out, ⟲ to reset

See [DRIVE_FEATURES.md](DRIVE_FEATURES.md) for complete documentation.

---

## Media Root

```
/storage/downloads/Movies/
```

This is a read-only source. The server never modifies, moves, or
deletes anything inside it.

Generated HLS cache lives in `~/media-server/cache/` — a completely
separate directory.

---

## Project Structure

```
media-server/
├── app.py                  ← entry point
├── config.py               ← all configuration
├── requirements.txt
├── README.md
├── DRIVE_FEATURES.md       ← personal drive documentation
│
├── media/
│   ├── models.py           ← data classes
│   ├── filesystem.py       ← safe path resolution + directory listing
│   └── scanner.py          ← per-request media discovery
│
├── transcoding/
│   ├── detector.py         ← ffprobe wrapper + metadata cache
│   ├── profiles.py         ← playback decision (transcode / direct)
│   ├── ffmpeg.py           ← FFmpeg command builder + launcher
│   └── manager.py          ← job queue, concurrency, state tracking
│
├── routes/
│   ├── browse.py           ← /browse/<path>
│   ├── playback.py         ← /player/<path> + /hls/<id>/<file>
│   ├── api.py              ← /api/status/<video_id>
│   ├── upload.py           ← /api/upload (file upload)
│   ├── delete.py           ← /api/delete (file/folder deletion)
│   └── folder.py           ← /api/folder/create (folder creation)
│
├── templates/
│   ├── base.html
│   ├── browse.html
│   └── player.html
│
└── static/
    ├── css/
    │   ├── style.css
    │   └── drive.css       ← personal drive styles
    └── js/
        ├── player.js
        ├── hls.min.js      ← YOU MUST ADD THIS (see Installation)
        ├── upload.js       ← file upload UI
        ├── delete.js       ← file deletion UI
        ├── menu.js         ← 3-dot menu + file preview
        └── folder.js       ← folder creation UI
```

---

## Installation (Termux)

### 1 — Grant storage access

```bash
termux-setup-storage
```

When prompted, tap **Allow**.

### 2 — Update packages

```bash
pkg update && pkg upgrade -y
```

### 3 — Install system dependencies

```bash
pkg install python ffmpeg -y
```

### 4 — Clone / copy the project

If you have this project as a zip, extract it to Termux home:

```bash
mkdir -p ~/media-server
# copy project files here
```

Or if using git:

```bash
pkg install git -y
git clone <your-repo-url> ~/media-server
```

### 5 — Install Python dependencies

```bash
cd ~/media-server
pip install -r requirements.txt
```

### 6 — Download HLS.js

The player requires `hls.js`. Download the minified build:

```bash
curl -L \
  "https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js" \
  -o ~/media-server/static/js/hls.min.js
```

> **No internet on the phone?** Download `hls.min.js` on another
> device and copy it to `static/js/` via USB or any file transfer.

Verify it arrived:

```bash
ls -lh ~/media-server/static/js/hls.min.js
```

### 7 — Verify FFmpeg is working

```bash
ffmpeg -version
ffprobe -version
```

Both should print version information. If not: `pkg install ffmpeg -y`

### 8 — Start the server

```bash
cd ~/media-server
python app.py
```

You will see a startup report similar to:

```
============================================
         TERMUX MEDIA SERVER
============================================

  Media root:  /storage/downloads/Movies
               ✓ Accessible

  FFmpeg:      ✓ Found
  FFprobe:     ✓ Found
  HLS.js:      ✓ Found

  Cache:       ✓ ~/media-server/cache

  Server:      http://192.168.1.42:8080
  Max jobs:    1

  Open the URL above in your browser.
  Press CTRL+C to stop the server.

============================================
```

Open the printed URL in your browser (on any device on the same Wi-Fi).

---

## Configuration

All settings live in `config.py`. Every setting can be overridden
with an environment variable of the same name:

### Media Server Settings

| Variable          | Default                        | Description                       |
|-------------------|--------------------------------|-----------------------------------|
| `MEDIA_ROOT`      | `/storage/downloads/Movies`    | Source media directory            |
| `PORT`            | `8080`                         | HTTP port                         |
| `HOST`            | `0.0.0.0`                      | Bind address                      |
| `MAX_TRANSCODES`  | `1`                            | Max simultaneous FFmpeg processes  |
| `HLS_SEGMENT_TIME`| `6`                            | Segment duration (seconds)        |
| `VIDEO_CRF`       | `23`                           | H.264 quality (18–28, lower=better)|
| `CACHE_DIR`       | `~/media-server/cache`         | HLS output directory              |
| `HLS_READY_TIMEOUT`| `120`                         | Seconds to wait for first segment |
| `DEBUG`           | `false`                        | Flask debug mode                  |

### Personal Drive Settings

| Variable          | Default                        | Description                       |
|-------------------|--------------------------------|-----------------------------------|
| `UPLOAD_ENABLED`  | `true`                         | Enable file uploads               |
| `DELETE_ENABLED`  | `true`                         | Enable file/folder deletion       |
| `MAX_UPLOAD_SIZE` | `524288000` (500 MB)           | Max upload file size in bytes     |
| `UPLOAD_PASSWORD` | `None`                         | Optional upload password          |
| `DELETE_PASSWORD` | `None`                         | Optional delete password          |

Example — custom media root and port:

```bash
MEDIA_ROOT=/sdcard/Films PORT=9090 python app.py
```

Example — enable password protection:

```bash
UPLOAD_PASSWORD=secret123 DELETE_PASSWORD=secret456 python app.py
```

---

## Cache Management

```bash
# Remove only incomplete / failed transcode entries
python app.py --cleanup-cache

# Remove ALL transcoded HLS cache (frees disk space)
# Original media is NEVER touched
python app.py --clear-cache

# Custom port
python app.py --port 9090
```

Cache location: `~/media-server/cache/hls/<video-id>/`

---

## Keeping the Server Running

Termux closes background processes when you switch apps.
Use one of these approaches:

### Option A — Termux:Task (recommended)
Install the Termux:Task add-on from F-Droid and create a task that
runs `python ~/media-server/app.py`.

### Option B — tmux (keeps running if Termux is backgrounded)

```bash
pkg install tmux -y
tmux new-session -s media
cd ~/media-server && python app.py
# Detach: press Ctrl+B then D
# Re-attach: tmux attach -t media
```

### Option C — Termux:Widget
Create a shortcut script in `~/.shortcuts/`:

```bash
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/media-server.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/media-server
python app.py
EOF
chmod +x ~/.shortcuts/media-server.sh
```

---

## How Playback Works

```
Browser clicks video
        ↓
/player/<path> route
        ↓
manager.submit() — non-blocking, returns immediately
        ↓
player.html sent to browser (shows "Preparing stream…")
        ↓
Background thread starts:
  [1] Acquire semaphore (MAX_TRANSCODES=1 ensures one at a time)
  [2] Run ffprobe — detect codecs
  [3] Launch FFmpeg → H.264/AAC HLS → cache/hls/<id>/
  [4] Poll for seg_000.ts
  [5] Set job state = READY
        ↓
Browser polls /api/status/<id> every 1.5 seconds
        ↓
When READY → load stream.m3u8 via hls.js
        ↓
Playback starts. FFmpeg continues generating segments in background.
        ↓
FFmpeg finishes → writes #EXT-X-ENDLIST → full VOD available
```

---

## Testing Checklist

### Test 1 — MP4 H.264/AAC

```
File: Movie.mp4 (H.264, AAC)
Expected: Plays immediately (fast transcode even though codec is H.264;
          direct-play optimization is Phase 2)
Diagnose: Check ~/media-server/logs/<id>.log if it fails
```

### Test 2 — MKV HEVC

```
File: Movie.mkv (HEVC/H.265)
Expected: Transcoded to H.264, plays successfully
Diagnose: FFmpeg log will show the encode happening
```

### Test 3 — 10-bit HEVC

```
File: Movie.mkv (HEVC 10-bit, yuv420p10le)
Expected: Transcoded to 8-bit H.264 (yuv420p forced in command)
Diagnose: ffprobe should show pix_fmt=yuv420p10le;
          output stream.m3u8 should work in Chrome
```

### Test 4 — Nested folders

```
Structure: /Movies/Series/Mr Robot/Season 1/ep01.mkv
Navigate:  Browse → Series → Mr Robot → Season 1 → ep01
Expected: Back button works at each level, file plays
```

### Test 5 — Filename with spaces and special characters

```
File: "The Movie (2023) [BluRay].mkv"
Expected: URL-encoded correctly, no 404 or 403
Diagnose: Check browser URL bar, check Flask request log
```

### Test 6 — New file added after startup

```
Add: /storage/downloads/Movies/NewMovie.mkv
Refresh: /browse/ in browser
Expected: NewMovie.mkv appears immediately
Note: No restart needed — scanning is per-request
```

### Test 7 — Seek

```
During playback, drag the seek bar
Expected: Video jumps to the new position
Note: Works once enough segments have been transcoded.
      Seeking past un-transcoded segments will stall briefly.
```

### Test 8 — Pause / Resume

```
Press pause → press play
Expected: Playback resumes from the same position
```

### Test 9 — Path traversal attempt

```
URL: http://phone:8080/browse/../../etc/passwd
Expected: HTTP 403 — safe_join() blocks it
```

### Test 10 — FFmpeg failure

```
Rename a media file after clicking it (so FFmpeg can't find it)
Expected: Job state → FAILED, player shows error message
Note: Failed jobs are removed from registry — refresh to retry
```

### Test 11 — Missing file

```
URL: http://phone:8080/player/nonexistent.mkv
Expected: HTTP 404
```

### Test 12 — Already-cached video

```
Play a video, wait for full transcode, restart the server, play again
Expected: Job immediately READY (cache hit), no re-transcode
```

---

## Troubleshooting

### "FFprobe not found" / "FFmpeg not found"

```bash
pkg install ffmpeg -y
ffmpeg -version   # should print version
```

### "Media root not found"

```bash
termux-setup-storage   # if not done yet
ls /storage/downloads/ # confirm your files are here
```

Or set a custom path:

```bash
MEDIA_ROOT=/path/to/your/movies python app.py
```

### "HLS.js not found"

```bash
curl -L "https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js" \
  -o ~/media-server/static/js/hls.min.js
```

### Video plays audio but no picture (or vice versa)

The HLS transcode puts both video and audio in the same `stream.m3u8`.
This should not happen with the default config. Check the FFmpeg log:

```bash
cat ~/media-server/logs/<video-id>.log | tail -30
```

### Transcoding is very slow

- `ultrafast` preset is already the fastest.
- Lower `VIDEO_CRF` increases quality but also CPU load (default 23 is good).
- Ensure no other heavy processes are running on the phone.
- High-resolution 4K content will always be slow on mobile CPUs.

### Player shows "Transcoding video…" forever

Check if FFmpeg is still running:

```bash
ps aux | grep ffmpeg
```

Read the FFmpeg log:

```bash
ls ~/media-server/logs/
cat ~/media-server/logs/<id>.log | tail -50
```

Common causes:
- Source file is unreadable (permissions)
- Source file is corrupted
- FFmpeg ran out of disk space

### Port 8080 already in use

```bash
python app.py --port 9090
```

### Finding your phone's IP

```bash
ip addr show | grep "inet " | grep -v "127.0.0.1"
```

---

## Phase Roadmap

| Phase | Feature                        | Status     |
|-------|--------------------------------|------------|
| 1     | Browse + universal transcode   | ✓ Done     |
| 2     | Direct-play (H.264/AAC MP4)    | Planned    |
| 3     | Cache size limits + auto-clean | Planned    |
| 4     | Subtitle rendering             | Planned    |
| 5     | Multiple audio track selection | Planned    |
| 6     | Metadata / posters / search    | Planned    |

---

## Security Notes

- **Path traversal**: all user-supplied paths go through `safe_join()`.
  Requests for `../../etc/passwd` return HTTP 403.
- **No shell=True**: all subprocess calls use explicit argument lists.
- **Only two roots are exposed**: `MEDIA_ROOT` (read-only) and
  `cache/hls/<id>/` (server-generated output).
- **LAN only**: the server binds to `0.0.0.0` and is intended for
  private home networks. Do not expose port 8080 to the internet.

---

## License

MIT — do whatever you want with it.
