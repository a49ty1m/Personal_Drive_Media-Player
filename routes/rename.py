"""
routes/rename.py

File and folder renaming handling.
"""

import os
from flask import Blueprint, request, jsonify

import config
from media.filesystem import safe_join

rename_bp = Blueprint("rename", __name__)


@rename_bp.route("/api/rename", methods=["POST"])
def rename_item():
    """
    Rename a file or folder.
    
    JSON body:
        {
            "path": "relative/path/to/file-or-folder",
            "new_name": "new-name"
        }
    
    Returns:
        JSON: {
            "success": true/false,
            "message": "human-readable message"
        }
    """
    data = request.get_json()
    
    if not data or "path" not in data or "new_name" not in data:
        return jsonify({
            "success": False,
            "message": "Missing path or new_name."
        }), 400
    
    old_path = data["path"]
    new_name = data["new_name"].strip()
    
    # Validate new name
    if not new_name:
        return jsonify({
            "success": False,
            "message": "New name cannot be empty."
        }), 400
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in new_name for char in invalid_chars):
        return jsonify({
            "success": False,
            "message": "Name contains invalid characters."
        }), 400
    
    # Prevent hidden files/folders
    if new_name.startswith('.'):
        return jsonify({
            "success": False,
            "message": "Name cannot start with a dot."
        }), 400
    
    # Security: Resolve paths safely
    try:
        old_full_path = safe_join(config.MEDIA_ROOT, old_path)
    except (ValueError, OSError):
        return jsonify({
            "success": False,
            "message": "Invalid path."
        }), 403
    
    # Check if source exists
    if not os.path.exists(old_full_path):
        return jsonify({
            "success": False,
            "message": "File or folder not found."
        }), 404
    
    # Prevent renaming MEDIA_ROOT itself
    if os.path.abspath(old_full_path) == os.path.abspath(config.MEDIA_ROOT):
        return jsonify({
            "success": False,
            "message": "Cannot rename the root media directory."
        }), 403
    
    # Construct new path (same parent directory, new name)
    parent_dir = os.path.dirname(old_full_path)
    new_full_path = os.path.join(parent_dir, new_name)
    
    # Check if target already exists
    if os.path.exists(new_full_path):
        return jsonify({
            "success": False,
            "message": "A file or folder with this name already exists."
        }), 400
    
    # Rename
    try:
        os.rename(old_full_path, new_full_path)
        
        item_type = "folder" if os.path.isdir(new_full_path) else "file"
        return jsonify({
            "success": True,
            "message": f"Successfully renamed {item_type}."
        })
    
    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Permission denied."
        }), 403
    
    except Exception:
        return jsonify({
            "success": False,
            "message": "Rename failed."
        }), 500
