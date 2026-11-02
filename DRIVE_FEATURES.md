# Personal Drive Features

Your media server has been upgraded to a full-featured personal cloud drive!

---

## 🔧 Recent Bug Fixes & Improvements

### v1.1 - Latest Updates
- ✅ **Fixed**: Removed duplicate upload button (was showing two buttons)
- ✅ **Fixed**: Zoom controls now only appear on PDFs (not on images)
- ✅ **Fixed**: Download button now positioned left of close button in preview
- ✅ **Improved**: Modal header layout with grouped action buttons
- ✅ **Improved**: Single, clean upload button in header
- ✅ **Improved**: Better button organization in preview modal

---

## 🎉 New Features

### 1. **File Upload**
- ✅ Drag & drop multiple files
- ✅ Click to browse and select files
- ✅ Upload progress bar
- ✅ Support for ALL file types (not just videos)
- ✅ Auto-rename if file exists
- ✅ Configurable file size limit (default: 500 MB)
- ✅ Optional password protection

### 2. **File Deletion**
- ✅ Delete files with one click
- ✅ Delete folders recursively
- ✅ Confirmation dialog before deletion
- ✅ Optional password protection
- ✅ Safe path validation
- ✅ 3-dot menu system (⋮)

### 3. **Folder Management**
- ✅ Create new folders with "📁 Create Folder" button
- ✅ Folder name validation (alphanumeric, spaces, dash, underscore, dot)
- ✅ Delete folders recursively
- ✅ Navigate folder hierarchy
- ✅ Visual feedback on creation
- ✅ Row layout matching file list
- ✅ Auto-refresh after creation

### 4. **File Preview System**
- ✅ Preview images (JPG, PNG, GIF, WebP, SVG, BMP, ICO)
- ✅ Preview text files with syntax highlighting (TXT, MD, JSON, XML, CSV, code files)
- ✅ Preview PDFs with zoom controls (50% - 300%)
- ✅ Preview audio files with built-in player (MP3, WAV, OGG, M4A, FLAC)
- ✅ Dark-themed preview modal
- ✅ Download button in every preview (left of close button)
- ✅ Fallback message for non-previewable files
- ✅ Click filename to preview
- ✅ Click video filename to play in video player
- ✅ Press Escape to close preview
- ✅ Click outside modal to close

### 5. **PDF Viewer Features**
- ✅ Zoom In (🔍+) - Increase by 25%
- ✅ Zoom Out (🔍−) - Decrease by 25%
- ✅ Reset Zoom (⟲) - Return to 100%
- ✅ Live zoom percentage display (e.g., "125%")
- ✅ Smooth zoom transitions
- ✅ Zoom range: 50% to 300%
- ✅ Auto-reset to 100% on close
- ✅ Zoom controls only shown for PDFs (not images)

### 6. **3-Dot Menu System**
- ✅ Clean context menu (⋮) for file/folder actions
- ✅ Download option
- ✅ Delete option with confirmation
- ✅ Open option for folders
- ✅ Prevents accidental actions
- ✅ High z-index to prevent overlapping
- ✅ Auto-close when clicking outside
- ✅ Smooth animations

### 7. **Enhanced File Browser**
- ✅ View ALL file types (documents, images, archives, code, etc.)
- ✅ File type icons (🎬 videos, 📄 documents, 🖼️ images, 🎵 audio, etc.)
- ✅ File size display (KB, MB, GB)
- ✅ Row layout for folders and files
- ✅ Direct download for non-video files
- ✅ Video streaming for video files
- ✅ Hover effects for better UX

### 8. **Security**
- ✅ Path traversal protection
- ✅ Optional upload password
- ✅ Optional delete password
- ✅ File size validation
- ✅ Secure filename handling
- ✅ Root directory protection

---

## 🚀 Usage

### Basic Usage (No Password)

1. **Browse Files**: Navigate through folders as usual
2. **Create Folder**: Click "📁 Create Folder" button
   - Enter folder name (letters, numbers, spaces, dash, underscore, dot)
   - Press Enter or click "Create"
3. **Upload Files**: Click "📤 Upload Files" button
   - Drag & drop files into the upload zone
   - Or click to browse and select files
   - Click "Upload" button
4. **Preview Files**: Click on filename
   - Images, text, PDFs, and audio files open in preview
   - Use zoom controls for PDFs (🔍+/🔍−/⟲)
   - Videos open in video player
5. **Download Files**: Click the 3-dot menu (⋮) → Download
6. **Delete Files/Folders**: Click the 3-dot menu (⋮) → Delete
   - Confirm deletion

### With Password Protection

Set environment variables before starting:

```bash
# Require password for uploads
UPLOAD_PASSWORD=mysecret python app.py

# Require password for deletions
DELETE_PASSWORD=mysecret python app.py

# Both
UPLOAD_PASSWORD=upload123 DELETE_PASSWORD=delete456 python app.py
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Upload settings
UPLOAD_ENABLED=true              # Enable/disable uploads (default: true)
MAX_UPLOAD_SIZE=524288000        # Max size in bytes (default: 500 MB)
UPLOAD_PASSWORD=secret           # Optional password (default: none)

# Delete settings
DELETE_ENABLED=true              # Enable/disable deletion (default: true)
DELETE_PASSWORD=secret           # Optional password (default: none)

# File browsing
MEDIA_ROOT=/path/to/files        # Root directory (default: parent of media-server)
```

### In config.py

```python
# Maximum upload file size (500 MB default)
MAX_UPLOAD_SIZE = 500 * 1024 * 1024

# Allow all file types (set to specific extensions to limit)
ALLOWED_UPLOAD_EXTENSIONS = None  # None = all types allowed

# File type categories for icons
FILE_CATEGORIES = {
    "video": {".mp4", ".mkv", ...},
    "audio": {".mp3", ".wav", ...},
    "image": {".jpg", ".png", ...},
    # ... etc
}
```

---

## 📁 Supported File Types

### Videos 🎬
`.mkv`, `.mp4`, `.webm`, `.m4v`, `.mov`, `.avi`, `.ts`, `.flv`, `.wmv`

### Audio 🎵
`.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`

### Images 🖼️
`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp`, `.ico`

### Documents 📄
`.pdf`, `.doc`, `.docx`, `.txt`, `.odt`, `.rtf`

### Spreadsheets 📊
`.xls`, `.xlsx`, `.csv`, `.ods`

### Presentations 📽️
`.ppt`, `.pptx`, `.odp`

### Archives 📦
`.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`

### Code 💻
`.py`, `.js`, `.html`, `.css`, `.java`, `.cpp`, `.c`, `.json`, `.xml`, `.yml`

### Other Files 📎
Any other file type will be displayed with a generic icon

---

## 🎨 UI Features

### Design
- **Dark Theme**: Modern dark interface for comfortable viewing
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Row Layout**: Consistent layout for folders and files
- **File Icons**: Visual file type identification
- **File Sizes**: Human-readable size display (KB, MB, GB)
- **Single Upload Button**: Clean header with no duplicates

### Interactions
- **Drag & Drop**: Modern file upload UX
- **Progress Indicator**: Real-time upload progress
- **3-Dot Menu**: Clean context menu for actions
- **Hover Effects**: Visual feedback on hover
- **Confirmation Dialogs**: Prevent accidental deletions
- **Preview Modal**: Full-screen preview with dark theme
- **PDF Zoom**: Zoom controls only for PDFs (not images)
- **Keyboard Shortcuts**: Escape to close modals

### Preview Modal Features
- **Dark Theme**: Black background for better viewing
- **Smart Layout**: Filename on left, controls on right
- **Button Order**: Zoom controls → Download → Close (left to right)
- **Download Button**: Green button positioned left of close button
- **Close Button**: Large X button to close, positioned at far right
- **Syntax Highlighting**: Code files with proper formatting
- **PDF Zoom**: Zoom in/out/reset with live percentage display
- **Audio Player**: Built-in audio player with controls
- **Image Viewer**: No zoom controls (use browser native zoom)
- **Text Preview**: 50KB limit for performance, syntax highlighted

---

## 🔒 Security Features

1. **Path Validation**: All paths are validated to prevent directory traversal attacks
2. **Secure Filenames**: Uploaded filenames are sanitized using `secure_filename()`
3. **Password Protection**: Optional password for uploads and deletions
4. **File Size Limits**: Configurable maximum upload size
5. **Root Protection**: Cannot delete the root media directory
6. **Folder Name Validation**: Only alphanumeric and safe characters allowed

---

## 🛠️ API Endpoints

### Upload
- `POST /api/upload` - Upload files
  - Form data: `files[]`, `path`, `password`
- `GET /api/upload/check` - Check upload status

### Delete
- `POST /api/delete` - Delete file/folder
  - JSON: `{"path": "...", "password": "..."}`
- `GET /api/delete/check` - Check delete status

### Folder
- `POST /api/folder/create` - Create new folder
  - JSON: `{"path": "...", "name": "..."}`

### Download
- `GET /download/<path>` - Download or preview file
  - Query param: `?download=true` - Force download

---

## 📝 Examples

### Create Folder
```javascript
fetch('/api/folder/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        path: '/Movies',
        name: 'New Folder'
    })
});
```

### Upload with Password
```javascript
const formData = new FormData();
formData.append('files[]', file);
formData.append('path', 'Movies/');
formData.append('password', 'mysecret');

fetch('/api/upload', {
    method: 'POST',
    body: formData
});
```

### Delete with Password
```javascript
fetch('/api/delete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        path: 'Movies/old-movie.mp4',
        password: 'mysecret'
    })
});
```

---

## 🐛 Troubleshooting

### Upload fails
- Check `MAX_UPLOAD_SIZE` in config
- Ensure `UPLOAD_ENABLED=true`
- Verify password if `UPLOAD_PASSWORD` is set
- Check disk space

### Delete fails
- Ensure `DELETE_ENABLED=true`
- Verify password if `DELETE_PASSWORD` is set
- Check file/folder permissions

### Folder creation fails
- Check folder name contains only valid characters
- Ensure folder doesn't already exist
- Verify write permissions

### Preview not working
- Browser must support the file type
- PDFs require browser PDF support
- Text files truncated at 50KB for performance
- Some file types don't support preview (download instead)

### PDF zoom not working
- Ensure browser supports PDF viewing
- Try downloading if preview fails
- Check browser console for errors

---

## 🎯 Features Summary

Your personal drive now includes:

1. ✅ **Upload** - Any file type, drag & drop, progress bar
2. ✅ **Download** - Direct download or force download
3. ✅ **Delete** - Files and folders with confirmation
4. ✅ **Create Folders** - With name validation
5. ✅ **Preview** - Images, text, PDFs, audio
6. ✅ **PDF Zoom** - 50% to 300% with controls
7. ✅ **3-Dot Menu** - Clean action menu
8. ✅ **Dark Theme** - Modern dark interface
9. ✅ **File Icons** - Visual file type identification
10. ✅ **File Sizes** - Human-readable display
11. ✅ **Security** - Password protection, path validation
12. ✅ **Video Streaming** - As before, with HLS transcoding

Enjoy your personal cloud drive! ☁️
