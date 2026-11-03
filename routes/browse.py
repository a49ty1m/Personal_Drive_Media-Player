"""
routes/browse.py

Directory listing and folder download routes.
"""

import os
import tempfile
import zipfile
import urllib.parse
import logging

from flask import Blueprint, render_template, abort, redirect, url_for, send_file, request

import config
from media.filesystem import safe_join, list_directory, get_file_icon, get_file_size, is_video_file

browse_bp = Blueprint("browse", __name__)
logger = logging.getLogger(__name__)


@browse_bp.route("/")
def root():
    return redirect(url_for("browse.browse"))


@browse_bp.route("/browse/")
@browse_bp.route("/browse/<path:path>")
def browse(path: str = ""):
    directory = safe_join(config.MEDIA_ROOT, path)

    if not os.path.isdir(directory):
        abort(404)

    folders, files = list_directory(directory)

    # ---- Parent URL ----
    parent = None
    if path:
        parent_rel = os.path.dirname(path)
        if parent_rel:
            parent = "/browse/" + urllib.parse.quote(parent_rel, safe="/")
        else:
            parent = "/browse/"

    # ---- Build URL-safe item dicts ----
    folder_items = [
        {
            "name": f.name,
            "url": "/browse/" + urllib.parse.quote(f.relative, safe="/"),
            "relative": f.relative,
        }
        for f in folders
    ]

    file_items = []
    for f in files:
        full_path = safe_join(config.MEDIA_ROOT, f.relative)
        icon = get_file_icon(f.extension)
        size = get_file_size(full_path)
        is_video = is_video_file(f.extension)
        
        file_items.append({
            "name": f.name,
            "url": "/player/" + urllib.parse.quote(f.relative, safe="/") if is_video else "/download/" + urllib.parse.quote(f.relative, safe="/"),
            "relative": f.relative,
            "icon": icon,
            "size": size,
            "is_video": is_video,
            "extension": f.extension,
        })

    title = os.path.basename(directory) if path else "My Drive"

    return render_template(
        "browse.html",
        title=title,
        parent=parent,
        folders=folder_items,
        files=file_items,
        path=path,
        upload_enabled=config.UPLOAD_ENABLED,
        delete_enabled=config.DELETE_ENABLED,
    )


@browse_bp.route("/download/<path:path>")
def download_file(path: str):
    """Download or preview file."""
    file_path = safe_join(config.MEDIA_ROOT, path)
    
    if not os.path.isfile(file_path):
        abort(404)
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    
    # Check if force download is requested
    force_download = request.args.get('download', 'false').lower() == 'true'
    
    # For PDFs, images, and text files - send inline for preview (unless forced)
    previewable_types = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', 
        '.txt', '.md', '.json', '.xml', '.log', '.csv'
    }
    
    if ext_lower in previewable_types and not force_download:
        # Send inline (for preview in browser)
        return send_file(file_path, as_attachment=False)
    else:
        # Send as attachment (force download)
        return send_file(file_path, as_attachment=True)


@browse_bp.route("/download-folder/<path:path>")
def download_folder(path: str):
    """Download a folder as a ZIP file."""
    folder_path = safe_join(config.MEDIA_ROOT, path)
    
    if not os.path.isdir(folder_path):
        abort(404)
    
    # Calculate folder size before creating ZIP
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            try:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
            except OSError:
                continue
    
    # Check if folder exceeds maximum ZIP size (if limit is set)
    if config.MAX_ZIP_SIZE > 0 and total_size > config.MAX_ZIP_SIZE:
        from flask import jsonify
        size_mb = total_size / (1024 * 1024)
        limit_mb = config.MAX_ZIP_SIZE / (1024 * 1024)
        logger.warning("Folder too large for ZIP: %.1f MB (limit: %.1f MB)", size_mb, limit_mb)
        return jsonify({
            "error": "Folder too large",
            "message": f"Folder is {size_mb:.1f} MB, exceeds {limit_mb:.0f} MB limit",
            "size_mb": round(size_mb, 1),
            "limit_mb": int(limit_mb)
        }), 413  # 413 Payload Too Large
    
    logger.info("Creating ZIP for folder: %s (%.1f MB, %d files)", 
                os.path.basename(folder_path), total_size / (1024 * 1024), file_count)
    
    # Create ZIP file in temp directory (not RAM)
    # delete=False so Flask can stream it, we'll clean up manually
    temp_zip = tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False)
    
    try:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Walk through directory and add all files
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path from the folder being zipped
                    arcname = os.path.relpath(file_path, folder_path)
                    try:
                        zf.write(file_path, arcname)
                    except (OSError, ValueError) as e:
                        # Skip files that can't be read
                        logger.warning("Skipping %s: %s", file_path, e)
                        continue
        
        # Get folder name for the ZIP filename
        folder_name = os.path.basename(folder_path) if path else "media"
        zip_filename = f"{folder_name}.zip"
        
        # Send the temp file and let Flask clean it up after sending
        return send_file(
            temp_zip.name,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_zip.name)
        except OSError:
            pass
        raise
