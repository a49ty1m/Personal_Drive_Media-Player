"""
routes/system_info.py - System information and statistics endpoint
"""

import os
import psutil
import platform
from flask import Blueprint, jsonify
import config

system_info_bp = Blueprint('system_info', __name__)


@system_info_bp.route("/api/system-info")
def get_system_info():
    """
    Return system information: CPU, RAM, storage, platform.
    """
    try:
        # CPU Information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        # Memory Information
        memory = psutil.virtual_memory()
        
        # Storage Information (media root)
        storage = psutil.disk_usage(config.MEDIA_ROOT)
        
        # Cache storage
        try:
            cache_storage = psutil.disk_usage(config.CACHE_DIR)
        except:
            cache_storage = None
        
        # System uptime
        boot_time = psutil.boot_time()
        from datetime import datetime
        uptime_seconds = datetime.now().timestamp() - boot_time
        
        # Platform info
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
        }
        
        # Active transcoding jobs
        from transcoding.manager import manager
        active_jobs = len(manager._registry)
        
        response = {
            "cpu": {
                "usage_percent": round(cpu_percent, 1),
                "cores": cpu_count,
                "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
            },
            "memory": {
                "total_mb": round(memory.total / (1024 * 1024), 0),
                "used_mb": round(memory.used / (1024 * 1024), 0),
                "available_mb": round(memory.available / (1024 * 1024), 0),
                "percent": round(memory.percent, 1),
            },
            "storage": {
                "media_root": {
                    "path": config.MEDIA_ROOT,
                    "total_gb": round(storage.total / (1024 * 1024 * 1024), 2),
                    "used_gb": round(storage.used / (1024 * 1024 * 1024), 2),
                    "free_gb": round(storage.free / (1024 * 1024 * 1024), 2),
                    "percent": round(storage.percent, 1),
                }
            },
            "cache": {
                "total_mb": round(cache_storage.total / (1024 * 1024), 0) if cache_storage else 0,
                "used_mb": round(cache_storage.used / (1024 * 1024), 0) if cache_storage else 0,
                "free_mb": round(cache_storage.free / (1024 * 1024), 0) if cache_storage else 0,
            },
            "system": system_info,
            "uptime_hours": round(uptime_seconds / 3600, 1),
            "active_transcodes": active_jobs,
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
