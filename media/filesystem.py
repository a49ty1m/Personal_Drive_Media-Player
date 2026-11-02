"""
media/filesystem.py

Safe path resolution and directory listing.
All user-supplied path segments must pass through safe_join()
before touching the filesystem.
"""

import os
import urllib.parse
from typing import Tuple, List

from flask import abort

import config
from media.models import Folder, MediaFile


def safe_join(root: str, relative: str) -> str:
    """
    Resolve root + relative into a safe absolute path.

    - Decodes percent-encoding in relative.
    - Normalises path separators.
    - Resolves symlinks to prevent escape via symbolic links.
    - Calls abort(403) if the resolved path would escape root.

    Never call os.path.join(root, user_input) directly — always use this.
    """
    root = os.path.realpath(root)

    # Decode any URL-encoded characters
    decoded = urllib.parse.unquote(relative)

    # Normalise Windows-style separators just in case
    decoded = decoded.replace("\\", "/")

    # Strip leading slashes so os.path.join doesn't treat it as absolute
    decoded = decoded.lstrip("/")

    resolved = os.path.realpath(os.path.join(root, decoded))

    # Must be exactly root, or a child of root
    if resolved != root and not resolved.startswith(root + os.sep):
        abort(403)

    return resolved


def list_directory(abs_path: str) -> Tuple[List[Folder], List[MediaFile]]:
    """
    List the contents of abs_path.

    Returns (folders, media_files):
        folders     — sorted alphabetically (case-insensitive)
        media_files — sorted alphabetically, now includes ALL file types

    Hidden files/folders (starting with '.') are skipped.
    """
    if not os.path.isdir(abs_path):
        abort(404)

    try:
        entries = sorted(os.listdir(abs_path), key=str.casefold)
    except PermissionError:
        abort(403)

    folders: List[Folder] = []
    media_files: List[MediaFile] = []

    # The app directory itself (media-server/) — never expose it in the listing
    # __file__ is media/filesystem.py, so two dirname()s = the media-server/ dir
    _app_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    for name in entries:
        if name.startswith("."):
            continue

        full = os.path.join(abs_path, name)

        # Hide the media-server app folder from the listing
        if os.path.isdir(full) and os.path.abspath(full) == _app_dir:
            continue

        relative = (
            os.path.relpath(full, config.MEDIA_ROOT)
            .replace(os.sep, "/")
        )

        if os.path.isdir(full):
            folders.append(Folder(name=name, relative=relative))

        elif os.path.isfile(full):
            _, ext = os.path.splitext(name)
            ext_lower = ext.lower()
            
            # If BROWSEABLE_EXTENSIONS is set, filter by it
            if config.BROWSEABLE_EXTENSIONS is not None:
                if ext_lower not in config.BROWSEABLE_EXTENSIONS:
                    continue
            
            # Add all files (not just videos)
            media_files.append(
                MediaFile(name=name, relative=relative, extension=ext_lower)
            )

    return folders, media_files



def get_file_icon(extension: str) -> str:
    """
    Return a specific Unicode icon for each file type.
    Each extension gets its own unique icon.
    
    Args:
        extension: File extension (e.g., ".mp4", ".pdf")
    
    Returns:
        Unicode symbol representing the specific file type
    """
    ext_lower = extension.lower()
    
    # Specific icon mapping for each file type
    icon_map = {
        # Video files
        '.mp4': '🎬',    # Movie clapper
        '.mkv': '🎞️',    # Film frames
        '.avi': '📹',    # Video camera
        '.mov': '🎥',    # Movie camera
        '.wmv': '📼',    # Videocassette
        '.flv': '▶️',    # Play button
        '.webm': '🌐',   # Web globe (web video)
        '.m4v': '📱',    # Mobile phone (mobile video)
        '.mpg': '🎦',    # Cinema
        '.mpeg': '🎦',   # Cinema
        '.3gp': '📲',    # Mobile phone with arrow
        
        # Audio files
        '.mp3': '🎵',    # Musical note
        '.flac': '🎼',   # Musical score (lossless)
        '.wav': '〰️',    # Wavy line (waveform)
        '.aac': '🎧',    # Headphone
        '.ogg': '🔊',    # Speaker high volume
        '.m4a': '🎶',    # Multiple musical notes
        '.wma': '📻',    # Radio
        '.opus': '🎙️',   # Studio microphone
        '.aiff': '🎺',   # Trumpet
        
        # Image files
        '.jpg': '🖼️',    # Framed picture
        '.jpeg': '🖼️',   # Framed picture
        '.png': '🏞️',    # National park
        '.gif': '🎨',    # Artist palette
        '.bmp': '🖌️',    # Paintbrush
        '.svg': '✏️',    # Pencil (vector)
        '.webp': '🌄',   # Sunrise over mountains
        '.tiff': '📷',   # Camera
        '.ico': '🎯',    # Direct hit (icon)
        '.heic': '📸',   # Camera with flash
        
        # Document files
        '.pdf': '📕',    # Closed book (red)
        '.txt': '📝',    # Memo
        '.md': '📋',     # Clipboard
        '.doc': '📘',    # Blue book
        '.docx': '📘',   # Blue book
        '.odt': '📗',    # Green book
        '.rtf': '📄',    # Page facing up
        
        # Spreadsheet files
        '.xlsx': '📊',   # Bar chart
        '.xls': '📈',    # Chart increasing
        '.csv': '📉',    # Chart decreasing
        '.ods': '🧮',    # Abacus
        
        # Presentation files
        '.pptx': '📽️',   # Film projector
        '.ppt': '🎞️',    # Film frames
        '.odp': '🖥️',    # Desktop computer
        
        # Archive files
        '.zip': '🗜️',    # Clamp (compression)
        '.tar': '📦',    # Package
        '.gz': '🗃️',     # Card file box
        '.bz2': '🗄️',    # File cabinet
        '.7z': '🗂️',     # Card index dividers
        '.rar': '📮',    # Postbox
        '.xz': '📬',     # Open mailbox
        
        # Code files - Python
        '.py': '🐍',     # Snake (Python)
        '.pyc': '⚙️',    # Gear (compiled Python)
        '.pyw': '🪟',    # Window (Python GUI)
        '.pyx': '⚡',    # Lightning (Cython)
        
        # Code files - Web
        '.html': '🌐',   # Globe with meridians
        '.htm': '🌍',    # Earth globe
        '.css': '🎨',    # Artist palette
        '.js': '⚡',     # Lightning (JavaScript)
        '.jsx': '⚛️',    # Atom (React)
        '.ts': '💠',     # Diamond (TypeScript)
        '.tsx': '💎',    # Gem stone (React+TS)
        '.json': '📋',   # Clipboard (data)
        '.xml': '🏷️',    # Label (markup)
        
        # Code files - Shell
        '.sh': '🐚',     # Spiral shell (shell script)
        '.bash': '💻',   # Laptop (bash)
        '.zsh': '⌨️',    # Keyboard (zsh)
        '.fish': '🐟',   # Fish (fish shell)
        
        # Code files - Other
        '.c': '©️',      # Copyright (C language)
        '.cpp': '➕',    # Plus (C++)
        '.h': '🔤',     # ABC (header)
        '.java': '☕',   # Hot beverage (Java)
        '.rs': '🦀',    # Crab (Rust)
        '.go': '🔵',    # Blue circle (Go)
        '.php': '🐘',   # Elephant (PHP)
        '.rb': '💎',    # Gem (Ruby)
        '.swift': '🦅',  # Eagle (Swift)
        '.kt': '🅺',    # K button (Kotlin)
        '.scala': '🔺',  # Red triangle (Scala)
        
        # Config files
        '.yaml': '⚙️',   # Gear
        '.yml': '⚙️',    # Gear
        '.toml': '🔧',   # Wrench
        '.ini': '📝',    # Memo
        '.conf': '🔩',   # Nut and bolt
        '.env': '🔐',    # Locked with key (environment)
        
        # Database
        '.sql': '🗄️',    # File cabinet
        '.db': '💾',     # Floppy disk
        '.sqlite': '📊',  # Bar chart
        
        # Other
        '.log': '📜',    # Scroll
        '.tmp': '⏳',    # Hourglass
        '.bak': '💾',    # Floppy disk (backup)
        '.iso': '💿',    # Optical disk
    }
    
    # Return specific icon if found, otherwise return default
    return icon_map.get(ext_lower, '📄')  # Default: page facing up


def get_file_size(abs_path: str) -> str:
    """
    Get human-readable file size.
    
    Args:
        abs_path: Absolute path to file
    
    Returns:
        Human-readable size string (e.g., "15.2 MB")
    """
    try:
        size = os.path.getsize(abs_path)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} PB"
    except (OSError, ValueError):
        return "Unknown"


def is_video_file(extension: str) -> bool:
    """Check if file extension is a video file."""
    return extension.lower() in config.VIDEO_EXTENSIONS
