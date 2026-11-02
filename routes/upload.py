"""
routes/upload.py

File upload handling.
"""

import os
from flask import Blueprint, request, jsonify, abort
from werkzeug.utils import secure_filename

import config
from media.filesystem import safe_join

upload_bp = Blueprint("upload", __name__)


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed.
    
    If ALLOWED_UPLOAD_EXTENSIONS is None, all files are allowed.
    """
    if config.ALLOWED_UPLOAD_EXTENSIONS is None:
        return True
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in config.ALLOWED_UPLOAD_EXTENSIONS


def check_password(password: str) -> bool:
    """Check if provided password matches configured password."""
    if config.UPLOAD_PASSWORD is None:
        return True  # No password required
    return password == config.UPLOAD_PASSWORD


@upload_bp.route("/api/upload", methods=["POST"])
def upload_file():
    """
    Upload one or more files to a specified directory.
    
    Form data:
        - files: One or more files (key: "files[]")
        - path: Target directory path (relative to MEDIA_ROOT)
        - password: Optional password if UPLOAD_PASSWORD is set
    
    Returns:
        JSON: {
            "success": true/false,
            "uploaded": ["file1.txt", "file2.mp4"],
            "failed": [{"name": "file3.txt", "error": "reason"}],
            "message": "human-readable summary"
        }
    """
    if not config.UPLOAD_ENABLED:
        return jsonify({
            "success": False,
            "message": "Upload is disabled on this server."
        }), 403
    
    # Check password if required
    if config.UPLOAD_PASSWORD:
        password = request.form.get("password", "")
        if not check_password(password):
            return jsonify({
                "success": False,
                "message": "Invalid password."
            }), 401
    
    # Get target path
    target_path = request.form.get("path", "")
    target_dir = safe_join(config.MEDIA_ROOT, target_path)
    
    if not os.path.isdir(target_dir):
        return jsonify({
            "success": False,
            "message": "Target directory does not exist."
        }), 400
    
    # Check if files were provided
    if "files[]" not in request.files:
        return jsonify({
            "success": False,
            "message": "No files provided."
        }), 400
    
    files = request.files.getlist("files[]")
    
    if not files or all(f.filename == "" for f in files):
        return jsonify({
            "success": False,
            "message": "No files selected."
        }), 400
    
    uploaded = []
    failed = []
    
    for file in files:
        if file.filename == "":
            continue
        
        filename = secure_filename(file.filename)
        
        # Check if file type is allowed
        if not allowed_file(filename):
            failed.append({
                "name": file.filename,
                "error": "File type not allowed"
            })
            continue
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > config.MAX_UPLOAD_SIZE:
            size_mb = config.MAX_UPLOAD_SIZE // (1024 * 1024)
            failed.append({
                "name": file.filename,
                "error": f"File too large (max {size_mb} MB)"
            })
            continue
        
        # Save file
        filepath = os.path.join(target_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            # Add number suffix
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(target_dir, filename)
                counter += 1
        
        try:
            file.save(filepath)
            uploaded.append(filename)
        except Exception as e:
            failed.append({
                "name": file.filename,
                "error": str(e)
            })
    
    success = len(uploaded) > 0
    
    if success and not failed:
        message = f"Successfully uploaded {len(uploaded)} file(s)."
    elif success and failed:
        message = f"Uploaded {len(uploaded)} file(s), {len(failed)} failed."
    else:
        message = f"All uploads failed ({len(failed)} file(s))."
    
    return jsonify({
        "success": success,
        "uploaded": uploaded,
        "failed": failed,
        "message": message
    }), 200 if success else 400


@upload_bp.route("/api/upload/check", methods=["GET"])
def check_upload_status():
    """
    Check if upload is enabled and if password is required.
    
    Returns:
        JSON: {
            "enabled": true/false,
            "password_required": true/false,
            "max_size_mb": number
        }
    """
    return jsonify({
        "enabled": config.UPLOAD_ENABLED,
        "password_required": config.UPLOAD_PASSWORD is not None,
        "max_size_mb": config.MAX_UPLOAD_SIZE // (1024 * 1024)
    })
