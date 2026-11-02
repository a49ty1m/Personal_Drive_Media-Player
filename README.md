# 🎬 Termux Media Server & Personal Cloud Drive

A lightweight, feature-rich media server and personal cloud storage solution that runs natively in **Termux on Android**. Stream videos, manage files, and access your personal drive from any browser on your local network.

> **No proot, no Docker, no systemd** — pure Python + FFmpeg running directly in Termux.

---

## ✨ Features Overview

### 🎥 Media Streaming
- **Universal Video Support** - Stream any video format (MKV, MP4, AVI, etc.)
- **Automatic Transcoding** - H.264/AAC HLS conversion via FFmpeg
- **Smart Caching** - Reuse transcoded videos, auto-invalidate on file changes
- **Multiple Audio Tracks** - Select from available audio streams
- **Subtitle Support** - Enable and switch between subtitle tracks
- **Non-blocking Playback** - Page loads instantly, stream starts ASAP

### 📁 File Management
- **Upload Files** - Drag & drop multiple files, support for all file types (500MB limit)
- **Download Files** - Direct download from 3-dot menu or preview modal
- **Delete Files & Folders** - Recursive deletion with confirmation dialogs
- **Rename Files & Folders** - Clean rename interface with validation
- **Create Folders** - Easy folder creation anywhere in the hierarchy
- **Smart Navigation** - Browse nested folder structures with breadcrumbs

### 👁️ File Preview System
- **Images** - JPG, PNG, GIF, WebP, SVG, BMP, ICO
- **Text Files** - Syntax-highlighted preview for TXT, MD, JSON, XML, CSV, code files
- **PDFs** - Embedded PDF viewer with browser-native controls
- **Audio** - Built-in player for MP3, WAV, OGG, M4A, FLAC
- **Videos** - Automatic redirect to video player with transcoding

### 🎨 Modern Interface
- **Dark Theme** - Comfortable viewing experience
- **3-Dot Menus** - Clean context menus with smart positioning (⋮)
- **Responsive Design** - Works on desktop, tablet, and mobile
- **File Type Icons** - Visual identification (🎬 videos, 📄 documents, 🖼️ images, 🎵 audio)
- **File Size Display** - Human-readable formats (KB, MB, GB)
- **Hover Effects** - Intuitive visual feedback

### 🔒 Security
- **Path Traversal Protection** - Prevents directory escape attacks
- **Password Protection** - Optional passwords for upload/delete operations
- **Timing Attack Prevention** - Secure password comparison using HMAC
- **Safe Filename Handling** - Automatic sanitization of uploaded filenames
- **File Size Validation** - Configurable upload limits
- **Root Directory Protection** - Cannot delete the media root

---

## 🚀 Quick Start

### Prerequisites

1. **Grant Storage Access**
```bash
termux-setup-storage
# Tap "Allow" when prompted
```

2. **Update Packages**
```bash
pkg update && pkg upgrade -y
```

3. **Install Dependencies**
```bash
pkg install python ffmpeg -y
```

### Installation

1. **Get the Project**
```bash
cd ~
git clone <your-repo-url> media-server
# Or extract from ZIP if you have it
```

2. **Install Python Dependencies**
```bash
cd ~/media-server
pip install -r requirements.txt
```

3. **Download HLS.js** (Required for video playback)
```bash
curl -L "https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js" \
  -o ~/media-server/static/js/hls.min.js
```

4. **Verify Installation**
```bash
ffmpeg -version
ffprobe -version
ls -lh ~/media-server/static/js/hls.min.js
```

5. **Start the Server**
```bash
cd ~/media-server
python app.py
```

You'll see output like:
```
============================================
         TERMUX MEDIA SERVER
============================================

  Media root:  /storage/downloads/Movies
               ✓ Accessible

  FFmpeg:      ✓ Found
  FFprobe:     ✓ Found
  HLS.js:      ✓ Found

  Cache:       ✓ /tmp/media-server/cache

  Server:      http://192.168.1.42:8080
  Max jobs:    1

  Open the URL above in your browser.
  Press CTRL+C to stop the server.

============================================
```

Open the URL in your browser and start using your media server!

---

## 📖 Usage Guide

### Browse & Navigate
1. Open `http://<your-phone-ip>:8080/browse/` in any browser
2. Click folders to navigate deeper
3. Click the "← Back" link to go up one level
4. Click file names to preview or play

### Upload Files
1. Click **"📤 Upload Files"** button
2. Drag and drop files into the upload zone, or click to browse
3. Click **"Upload"** to start
4. Wait for the progress bar to complete

### Create Folders
1. Navigate to the desired parent directory
2. Click **"📁 Create Folder"** button
3. Enter a folder name (letters, numbers, spaces, `-`, `_`, `.`)
4. Press **Enter** or click **"Create"**

### Preview Files
1. Click on any file name
2. **Images** - Full-screen preview with download option
3. **Text/Code** - Syntax-highlighted view (50KB limit)
4. **PDFs** - Embedded viewer with native browser controls
5. **Audio** - Built-in player with playback controls
6. **Videos** - Redirects to video player with transcoding

### Download Files
- **Method 1**: Click 3-dot menu (⋮) → **Download**
- **Method 2**: Preview the file → Click **Download** button

### Rename Files/Folders
1. Click 3-dot menu (⋮) → **✏️ Rename**
2. Enter new name (filename without extension is auto-selected)
3. Press **Enter** or click **"Rename"**

### Delete Files/Folders
1. Click 3-dot menu (⋮) → **🗑️ Delete**
2. Confirm deletion in the dialog
3. Folders are deleted recursively

### Play Videos
1. Click on any video file name
2. Wait for "Preparing stream..." message
3. Playback begins automatically once first segments are ready
4. Use player controls for play/pause, seek, volume
5. Select audio tracks or subtitles if available

---

## ⚙️ Configuration

All settings in `config.py` can be overridden with environment variables:

### Core Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDIA_ROOT` | Parent of media-server dir | Root directory for media files |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8080` | HTTP port |
| `DEBUG` | `false` | Flask debug mode |

### Transcoding Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TRANSCODES` | `1` | Max simultaneous FFmpeg processes |
| `HLS_SEGMENT_TIME` | `6` | Segment duration in seconds |
| `VIDEO_CRF` | `23` | H.264 quality (18-28, lower=better) |
| `CACHE_DIR` | `/tmp/media-server/cache` | HLS output directory |
| `HLS_READY_TIMEOUT` | `120` | Timeout for first segment (seconds) |

### Upload Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_ENABLED` | `true` | Enable/disable file uploads |
| `MAX_UPLOAD_SIZE` | `524288000` (500 MB) | Max upload size in bytes |
| `UPLOAD_PASSWORD` | `None` | Optional password for uploads |

### Delete Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DELETE_ENABLED` | `true` | Enable/disable deletion |
| `DELETE_PASSWORD` | `None` | Optional password for deletions |

### Example: Custom Configuration

```bash
# Custom media root and port
MEDIA_ROOT=/sdcard/Films PORT=9090 python app.py

# Enable password protection
UPLOAD_PASSWORD=secret123 DELETE_PASSWORD=secret456 python app.py

# Adjust transcoding quality
VIDEO_CRF=20 MAX_TRANSCODES=2 python app.py
```

---

## 🗂️ Project Structure

```
media-server/
├── app.py                      # Main entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── media/
│   ├── models.py              # Data classes
│   ├── filesystem.py          # Safe path resolution & listing
│   └── (scanner.py removed)   # Dead code eliminated
│
├── transcoding/
│   ├── detector.py            # FFprobe wrapper & metadata cache
│   ├── ffmpeg.py              # FFmpeg command builder
│   ├── manager.py             # Job queue & state tracking
│   └── (profiles.py removed)  # Dead code eliminated
│
├── routes/
│   ├── browse.py              # File browser
│   ├── playback.py            # Video player & HLS streaming
│   ├── api.py                 # Status API
│   ├── upload.py              # File upload API
│   ├── delete.py              # File/folder deletion API
│   ├── folder.py              # Folder creation API
│   └── download.py            # File download & preview
│
├── templates/
│   ├── base.html              # Base template
│   ├── browse.html            # File browser UI
│   └── player.html            # Video player UI
│
└── static/
    ├── css/
    │   ├── style.css          # Main styles
    │   └── drive.css          # File management styles
    └── js/
        ├── player.js          # Video player logic
        ├── hls.min.js         # HLS.js library (download required)
        ├── upload.js          # Upload UI
        ├── delete.js          # Delete UI
        ├── menu.js            # 3-dot menus & preview
        ├── folder.js          # Folder creation UI
        └── rename.js          # Rename UI
```

---

## 🎯 How Video Playback Works

```
1. User clicks video → /player/<path>
                          ↓
2. manager.submit() (non-blocking, returns immediately)
                          ↓
3. Player HTML sent to browser (shows "Preparing stream...")
                          ↓
4. Background thread starts:
   • Acquire semaphore (MAX_TRANSCODES limit)
   • Run ffprobe → detect codecs
   • Launch FFmpeg → transcode to H.264/AAC HLS
   • Output to /tmp/media-server/cache/hls/<video-id>/
   • Poll for first segment (seg_000.ts)
   • Set job state = READY
                          ↓
5. Browser polls /api/status/<video-id> every 1.5s
                          ↓
6. When READY → load stream.m3u8 via HLS.js
                          ↓
7. Playback starts
                          ↓
8. FFmpeg continues generating segments in background
                          ↓
9. FFmpeg finishes → writes #EXT-X-ENDLIST → full VOD available
```

**Cache Strategy:**
- First play: full transcode
- Subsequent plays: instant playback from cache
- File modified (mtime changed): auto-retranscode
- Cache location: `/tmp/media-server/cache/hls/<video-id>/`

---

## 🛡️ Security Features

### Path Traversal Protection
- All paths validated through `safe_join()`
- Attempts to access `../../etc/passwd` return HTTP 403
- Symlinks outside MEDIA_ROOT are blocked

### Password Protection
- Optional `UPLOAD_PASSWORD` and `DELETE_PASSWORD`
- Timing-attack-resistant comparison using `hmac.compare_digest()`
- No passwords stored; checked per-request only

### Safe File Handling
- Filenames sanitized using `secure_filename()`
- Non-ASCII filenames properly handled
- Race condition protection for concurrent uploads
- File size validation before upload

### XSS Prevention
- All user inputs properly escaped in templates
- File names sanitized before display
- No inline script execution

### Information Disclosure Prevention
- Generic error messages (no filesystem paths exposed)
- Detailed errors only in server logs
- Root directory cannot be deleted

---

## 🐛 Troubleshooting

### Server Won't Start

**"FFmpeg not found"**
```bash
pkg install ffmpeg -y
ffmpeg -version  # Verify installation
```

**"Media root not found"**
```bash
termux-setup-storage
ls /storage/downloads/  # Verify path exists

# Or set custom path
MEDIA_ROOT=/path/to/your/movies python app.py
```

**"Port 8080 already in use"**
```bash
python app.py --port 9090
```

### Upload Issues

**"Upload fails" / "Permission denied"**
```bash
# Check write permissions
ls -la /storage/downloads/Movies/

# Ensure UPLOAD_ENABLED is true
grep UPLOAD_ENABLED config.py
```

**"File size too large"**
```bash
# Increase limit (e.g., 1GB)
MAX_UPLOAD_SIZE=1073741824 python app.py
```

### Video Playback Issues

**"HLS.js not found"**
```bash
curl -L "https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js" \
  -o ~/media-server/static/js/hls.min.js
```

**"Video shows 'Preparing stream...' forever"**
```bash
# Check if FFmpeg is running
ps aux | grep ffmpeg

# Check FFmpeg logs
ls /tmp/media-server/logs/
tail -50 /tmp/media-server/logs/<video-id>_video.log

# Common causes:
# - Source file corrupted
# - Insufficient disk space
# - FFmpeg crashed
```

**"Playback is very slow"**
- `ultrafast` preset already used (fastest option)
- High-resolution 4K videos are CPU-intensive on mobile
- Lower `VIDEO_CRF` (e.g., 28) for faster but lower quality
- Ensure no other heavy processes running

**"Seeking is slow"**
- Known limitation: seeking requires re-transcoding from that point
- Wait time depends on phone CPU performance
- Pre-transcoded segments seek instantly

### File Management Issues

**"Folder created in wrong location"**
- Bug fixed in latest version
- Ensure you're running updated code
- Check browser console for JavaScript errors

**"Delete not working"**
```bash
# Check DELETE_ENABLED
grep DELETE_ENABLED config.py

# Verify password if set
DELETE_PASSWORD=yourpass python app.py
```

### Find Your Phone's IP

```bash
ip addr show | grep "inet " | grep -v "127.0.0.1"
# Or
ifconfig | grep "inet " | grep -v "127.0.0.1"
```

---

## 🔄 Keep Server Running

Termux kills background processes when you switch apps. Use one of these methods:

### Method 1: Termux:Task (Recommended)
1. Install **Termux:Task** from F-Droid
2. Create a task that runs: `python ~/media-server/app.py`
3. Run the task from home screen widget

### Method 2: tmux
```bash
pkg install tmux -y
tmux new-session -s media
cd ~/media-server && python app.py

# Detach: Ctrl+B then D
# Re-attach: tmux attach -t media
```

### Method 3: Termux:Widget
```bash
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/media-server.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/media-server
python app.py
EOF
chmod +x ~/.shortcuts/media-server.sh
```

Add Termux:Widget to home screen, tap the script to start.

---

## 🧹 Cache Management

### View Cache Size
```bash
du -sh /tmp/media-server/cache/
```

### Clean Up Failed Jobs
```bash
python app.py --cleanup-cache
```

### Clear ALL Cache (frees disk space)
```bash
python app.py --clear-cache
# Original media files are NEVER touched
```

### Automatic Cache Invalidation
- Files are automatically re-transcoded if modified
- Based on file `mtime` (modification time)
- No manual intervention needed

---

## 📋 Supported File Types

### Videos 🎬
`.mkv`, `.mp4`, `.webm`, `.m4v`, `.mov`, `.avi`, `.ts`, `.flv`, `.wmv`, `.mpg`, `.mpeg`

### Audio 🎵
`.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`, `.opus`

### Images 🖼️
`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp`, `.ico`

### Documents 📄
`.pdf`, `.doc`, `.docx`, `.txt`, `.odt`, `.rtf`, `.md`

### Spreadsheets 📊
`.xls`, `.xlsx`, `.csv`, `.ods`

### Presentations 📽️
`.ppt`, `.pptx`, `.odp`

### Archives 📦
`.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`

### Code 💻
`.py`, `.js`, `.html`, `.css`, `.java`, `.cpp`, `.c`, `.h`, `.json`, `.xml`, `.yml`, `.yaml`, `.sh`, `.go`, `.rs`, `.ts`, `.tsx`, `.jsx`

### Other Files 📎
All other files display with a generic icon and can be downloaded.

---

## 🧪 Testing

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing procedures covering:
- Security fixes (XSS, path traversal, timing attacks)
- Functionality tests (upload, delete, preview, playback)
- Resource leak tests (file handles, sockets)
- Configuration validation
- Performance benchmarks

---

## 🗺️ Feature Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Universal transcoding + browse | ✅ Complete |
| 2 | File upload/download/delete | ✅ Complete |
| 3 | Folder management | ✅ Complete |
| 4 | File preview system | ✅ Complete |
| 5 | Subtitle support | ✅ Complete |
| 6 | Multiple audio tracks | ✅ Complete |
| 7 | Smart menu positioning | ✅ Complete |
| 8 | Rename functionality | ✅ Complete |
| 9 | Password protection | ✅ Complete |
| 10 | Direct-play (H.264/AAC) | 🔄 Planned |
| 11 | Auto cache cleanup | 🔄 Planned |
| 12 | Metadata/posters | 🔄 Planned |
| 13 | Search functionality | 🔄 Planned |

---

## 📚 Additional Documentation

- **[DRIVE_FEATURES.md](DRIVE_FEATURES.md)** - Detailed personal drive feature documentation
- **[SMART_MENU_POSITIONING.md](SMART_MENU_POSITIONING.md)** - Technical details on menu positioning algorithm
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing procedures and checklists

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Direct playback for compatible videos (skip transcoding)
- Better mobile UI optimizations
- Thumbnail generation for videos
- Metadata extraction and display
- Search and filtering
- User authentication system

---

## 📄 License

MIT License - do whatever you want with it.

---

## 🙏 Credits

Built with:
- **Python** - Core application
- **Flask** - Web framework
- **FFmpeg** - Video transcoding
- **HLS.js** - Video streaming in browser
- **Termux** - Android terminal environment

---

## 📞 Support

Having issues? Check:
1. **Troubleshooting section** above
2. **Server logs**: `/tmp/media-server/logs/`
3. **Browser console**: Press F12 in browser
4. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** for test procedures

---

**Enjoy your personal media server and cloud drive!** ☁️🎬

*Last Updated: November 3, 2026*
