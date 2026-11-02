"""
routes/folder.py

Folder creation handling.
"""

import os
from flask import Blueprint, request, jsonify

import config
from media.filesystem import safe_join

folder_bp = Blueprint("folder", __name__)


@folder_bp.route("/api/folder/create", methods=["POST"])
def create_folder():
    """
    Create a new folder.
    
    JSON body:
        {
            "path": "relative/path/to/parent",
            "name": "new-folder-name"
        }
    
    Returns:
        JSON: {
            "success": true/false,
            "message": "human-readable message"
        }
    """
    data = request.get_json()
    
    if not data or "name" not in data:
        return jsonify({
            "success": False,
            "message": "No folder name provided."
        }), 400
    
    parent_path = data.get("path", "")
    folder_name = data["name"].strip()
    
    # Validate folder name
    if not folder_name:
        return jsonify({
            "success": False,
            "message": "Folder name cannot be empty."
        }), 400
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in folder_name for char in invalid_chars):
        return jsonify({
            "success": False,
            "message": "Folder name contains invalid characters."
        }), 400
    
    # Prevent hidden folders
    if folder_name.startswith('.'):
        return jsonify({
            "success": False,
            "message": "Folder name cannot start with a dot."
        }), 400
    
    # Security: Resolve path safely
    try:
        parent_dir = safe_join(config.MEDIA_ROOT, parent_path)
    except:
        return jsonify({
            "success": False,
            "message": "Invalid parent path."
        }), 403
    
    # Check if parent directory exists
    if not os.path.isdir(parent_dir):
        return jsonify({
            "success": False,
            "message": "Parent directory does not exist."
        }), 404
    
    # Create full path for new folder
    new_folder_path = os.path.join(parent_dir, folder_name)
    
    # Check if folder already exists
    if os.path.exists(new_folder_path):
        return jsonify({
            "success": False,
            "message": "A folder or file with this name already exists."
        }), 400
    
    # Create folder
    try:
        os.makedirs(new_folder_path)
        return jsonify({
            "success": True,
            "message": f"Folder '{folder_name}' created successfully."
        })
    
    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Permission denied."
        }), 403
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500
