"""
routes/favorites.py

Starred files and recently accessed files routes.
"""

import os
import json
import time
import urllib.parse
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, session

import config
from media.filesystem import safe_join, get_file_icon, get_file_size, is_video_file

favorites_bp = Blueprint("favorites", __name__)

# File to store starred files (per-session, could be upgraded to database)
STARRED_FILE = os.path.join(config.CACHE_DIR, "starred.json")
RECENT_FILE = os.path.join(config.CACHE_DIR, "recent.json")


def load_starred():
    """Load starred files from JSON."""
    if os.path.exists(STARRED_FILE):
        try:
            with open(STARRED_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_starred(starred_list):
    """Save starred files to JSON."""
    os.makedirs(os.path.dirname(STARRED_FILE), exist_ok=True)
    try:
        with open(STARRED_FILE, 'w') as f:
            json.dump(starred_list, f, indent=2)
    except OSError:
        pass


def load_recent():
    """Load recent files from JSON."""
    if os.path.exists(RECENT_FILE):
        try:
            with open(RECENT_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_recent(recent_list):
    """Save recent files to JSON."""
    os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)
    try:
        with open(RECENT_FILE, 'w') as f:
            json.dump(recent_list, f, indent=2)
    except OSError:
        pass


def add_to_recent(file_path):
    """Add a file to recent list (files only, no folders)."""
    # Safety check: Only add files, not folders
    full_path = safe_join(config.MEDIA_ROOT, file_path)
    if not os.path.isfile(full_path):
        return  # Skip if it's a folder or doesn't exist
    
    recent = load_recent()
    
    # Remove if already exists
    recent = [item for item in recent if item['path'] != file_path]
    
    # Add to front with timestamp
    recent.insert(0, {
        'path': file_path,
        'timestamp': time.time()
    })
    
    # Keep only last 50 items
    recent = recent[:50]
    
    save_recent(recent)


@favorites_bp.route("/starred/")
def starred():
    """Show starred files and folders."""
    starred_list = load_starred()
    
    # Build file and folder items
    file_items = []
    folder_items = []
    
    for item in starred_list:
        path = item['path']
        full_path = safe_join(config.MEDIA_ROOT, path)
        
        # Check if it's a folder or file
        if os.path.isdir(full_path):
            folder_items.append({
                "name": os.path.basename(path),
                "url": "/browse/" + urllib.parse.quote(path, safe="/"),
                "relative": path,
            })
        elif os.path.isfile(full_path):
            _, ext = os.path.splitext(full_path)
            icon = get_file_icon(ext)
            size = get_file_size(full_path)
            is_video = is_video_file(ext)
            
            file_items.append({
                "name": os.path.basename(path),
                "url": "/player/" + urllib.parse.quote(path, safe="/") if is_video else "/download/" + urllib.parse.quote(path, safe="/"),
                "relative": path,
                "icon": icon,
                "size": size,
                "is_video": is_video,
                "extension": ext,
            })
    
    return render_template(
        "browse.html",
        title="⭐ Starred",
        parent="/browse/",
        folders=folder_items,
        files=file_items,
        path="starred",
        upload_enabled=False,
        delete_enabled=config.DELETE_ENABLED,
    )


@favorites_bp.route("/recent/")
def recent():
    """Show recently accessed files (files only, no folders)."""
    recent_list = load_recent()
    
    # Build file items (and clean up any folders that might be in the list)
    file_items = []
    cleaned_recent = []
    
    for item in recent_list:
        file_path = item['path']
        full_path = safe_join(config.MEDIA_ROOT, file_path)
        
        # Skip if it's a folder
        if os.path.isdir(full_path):
            continue
        
        # Check if file still exists
        if not os.path.isfile(full_path):
            continue
        
        # Keep in cleaned list
        cleaned_recent.append(item)
        
        _, ext = os.path.splitext(full_path)
        icon = get_file_icon(ext)
        size = get_file_size(full_path)
        is_video = is_video_file(ext)
        
        file_items.append({
            "name": os.path.basename(file_path),
            "url": "/player/" + urllib.parse.quote(file_path, safe="/") if is_video else "/download/" + urllib.parse.quote(file_path, safe="/"),
            "relative": file_path,
            "icon": icon,
            "size": size,
            "is_video": is_video,
            "extension": ext,
        })
    
    # Save cleaned list if it changed
    if len(cleaned_recent) != len(recent_list):
        save_recent(cleaned_recent)
    
    return render_template(
        "browse.html",
        title="🕒 Recent Files",
        parent="/browse/",
        folders=[],
        files=file_items,
        path="recent",
        upload_enabled=False,
        delete_enabled=config.DELETE_ENABLED,
    )


@favorites_bp.route("/api/star/<path:file_path>", methods=["POST"])
def toggle_star(file_path):
    """Toggle starred status of a file."""
    starred = load_starred()
    
    # Check if already starred
    is_starred = any(item['path'] == file_path for item in starred)
    
    if is_starred:
        # Remove from starred
        starred = [item for item in starred if item['path'] != file_path]
        action = "removed"
    else:
        # Add to starred
        starred.append({
            'path': file_path,
            'timestamp': time.time()
        })
        action = "added"
    
    save_starred(starred)
    
    return jsonify({
        "success": True,
        "action": action,
        "is_starred": not is_starred
    })


@favorites_bp.route("/api/is_starred/<path:file_path>")
def check_starred(file_path):
    """Check if a file is starred."""
    starred = load_starred()
    is_starred = any(item['path'] == file_path for item in starred)
    
    return jsonify({
        "is_starred": is_starred
    })
