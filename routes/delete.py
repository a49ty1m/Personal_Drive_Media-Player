"""
routes/delete.py

File and folder deletion handling.
"""

import os
import shutil
from flask import Blueprint, request, jsonify

import config
from media.filesystem import safe_join

delete_bp = Blueprint("delete", __name__)


def check_password(password: str) -> bool:
    """Check if provided password matches configured password."""
    import hmac
    if config.DELETE_PASSWORD is None:
        return True  # No password required
    return hmac.compare_digest(password, config.DELETE_PASSWORD)


@delete_bp.route("/api/delete", methods=["POST"])
def delete_item():
    """
    Delete a file or folder.
    
    JSON body:
        {
            "path": "relative/path/to/file-or-folder",
            "password": "optional-password"
        }
    
    Returns:
        JSON: {
            "success": true/false,
            "message": "human-readable message"
        }
    """
    if not config.DELETE_ENABLED:
        return jsonify({
            "success": False,
            "message": "Deletion is disabled on this server."
        }), 403
    
    data = request.get_json()
    
    if not data or "path" not in data:
        return jsonify({
            "success": False,
            "message": "No path provided."
        }), 400
    
    # Check password if required
    if config.DELETE_PASSWORD:
        password = data.get("password", "")
        if not check_password(password):
            return jsonify({
                "success": False,
                "message": "Invalid password."
            }), 401
    
    target_path = data["path"]
    
    # Security: Resolve path safely
    try:
        full_path = safe_join(config.MEDIA_ROOT, target_path)
    except (ValueError, OSError):
        return jsonify({
            "success": False,
            "message": "Invalid path."
        }), 403
    
    # Check if path exists
    if not os.path.exists(full_path):
        return jsonify({
            "success": False,
            "message": "File or folder not found."
        }), 404
    
    # Prevent deletion of MEDIA_ROOT itself
    if os.path.abspath(full_path) == os.path.abspath(config.MEDIA_ROOT):
        return jsonify({
            "success": False,
            "message": "Cannot delete the root media directory."
        }), 403
    
    # Delete
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            item_type = "file"
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
            item_type = "folder"
        else:
            return jsonify({
                "success": False,
                "message": "Invalid item type."
            }), 400
        
        return jsonify({
            "success": True,
            "message": f"Successfully deleted {item_type}."
        })
    
    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Permission denied."
        }), 403
    
    except Exception:
        return jsonify({
            "success": False,
            "message": "Deletion failed."
        }), 500


@delete_bp.route("/api/delete/check", methods=["GET"])
def check_delete_status():
    """
    Check if deletion is enabled and if password is required.
    
    Returns:
        JSON: {
            "enabled": true/false,
            "password_required": true/false
        }
    """
    return jsonify({
        "enabled": config.DELETE_ENABLED,
        "password_required": config.DELETE_PASSWORD is not None
    })
