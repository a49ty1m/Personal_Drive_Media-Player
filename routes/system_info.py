"""
routes/system_info.py - System information and statistics endpoint
Optimized for Android/Termux - CPU stats removed (not supported)
"""

import os
import time
import platform
import logging
from flask import Blueprint, jsonify
import config

system_info_bp = Blueprint('system_info', __name__)
logger = logging.getLogger("media-server")

# Track server start time for uptime (works on all platforms including Android)
SERVER_START_TIME = time.time()

# Try to import psutil, make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("psutil loaded successfully")
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system stats will be disabled")


def _get_ram_android():
    """Read RAM from /proc/meminfo — works on Android without root."""
    try:
        info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    info[parts[0].rstrip(':')] = int(parts[1])  # kB
        total_mb = info.get('MemTotal', 0) / 1024
        available_mb = info.get('MemAvailable', 0) / 1024
        used_mb = total_mb - available_mb
        percent = round((used_mb / total_mb * 100), 1) if total_mb > 0 else 0
        return {
            'total_mb': round(total_mb),
            'used_mb': round(used_mb),
            'available_mb': round(available_mb),
            'percent': percent
        }
    except Exception as e:
        logger.warning(f"Cannot read /proc/meminfo: {e}")
        return {'total_mb': 0, 'used_mb': 0, 'available_mb': 0, 'percent': 0}


def _get_storage_android(path):
    """Use os.statvfs — works on Android for any accessible path."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        percent = round((used / total * 100), 1) if total > 0 else 0
        return {
            'total_gb': round(total / 1024**3, 2),
            'used_gb': round(used / 1024**3, 2),
            'free_gb': round(free / 1024**3, 2),
            'percent': percent
        }
    except Exception as e:
        logger.warning(f"os.statvfs failed for {path}: {e}")
        return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}


@system_info_bp.route("/api/system-info")
def get_system_info():
    """
    Return system information: RAM, storage, uptime, active jobs.
    CPU stats removed (not supported on Android/Termux).
    Falls back gracefully if psutil is not available or returns zeros.
    """
    try:
        # --- Memory ---
        mem = {'total_mb': 0, 'used_mb': 0, 'available_mb': 0, 'percent': 0}
        if PSUTIL_AVAILABLE:
            try:
                raw = psutil.virtual_memory()
                if raw.total > 0:
                    mem = {
                        'total_mb': round(raw.total / 1024**2),
                        'used_mb': round(raw.used / 1024**2),
                        'available_mb': round(raw.available / 1024**2),
                        'percent': round(raw.percent, 1),
                    }
                else:
                    logger.debug("psutil.virtual_memory() returned 0 — using /proc/meminfo fallback")
                    mem = _get_ram_android()
            except Exception as e:
                logger.warning(f"psutil memory failed: {e} — using /proc/meminfo fallback")
                mem = _get_ram_android()
        else:
            mem = _get_ram_android()

        # --- Storage ---
        stor = {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}
        if PSUTIL_AVAILABLE:
            try:
                raw_s = psutil.disk_usage(config.MEDIA_ROOT)
                if raw_s.total > 0:
                    stor = {
                        'total_gb': round(raw_s.total / 1024**3, 2),
                        'used_gb': round(raw_s.used / 1024**3, 2),
                        'free_gb': round(raw_s.free / 1024**3, 2),
                        'percent': round(raw_s.percent, 1),
                    }
                else:
                    logger.debug("psutil.disk_usage() returned 0 — using os.statvfs fallback")
                    stor = _get_storage_android(config.MEDIA_ROOT)
            except Exception as e:
                logger.warning(f"psutil disk_usage failed: {e} — using os.statvfs fallback")
                stor = _get_storage_android(config.MEDIA_ROOT)
        else:
            stor = _get_storage_android(config.MEDIA_ROOT)

        # --- Uptime (always use server start time — works on all platforms) ---
        uptime_seconds = time.time() - SERVER_START_TIME

        # --- Platform info ---
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
        }

        # --- Active transcoding jobs ---
        try:
            from transcoding.manager import manager
            active_jobs = len(manager._registry)
        except Exception as e:
            logger.error(f"Error getting active jobs: {e}")
            active_jobs = 0

        response = {
            "memory": mem,
            "storage": {
                "media_root": {
                    "path": config.MEDIA_ROOT,
                    **stor,
                }
            },
            "system": system_info,
            "uptime_hours": round(uptime_seconds / 3600, 1),
            "active_transcodes": active_jobs,
            "psutil_available": PSUTIL_AVAILABLE,
        }

        logger.debug(f"System stats: RAM {mem['percent']}%, Storage {stor['percent']}%")
        return jsonify(response)

    except Exception as e:
        logger.error(f"System info endpoint error: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "psutil_available": PSUTIL_AVAILABLE,
            "message": "Error fetching system info. Check server logs."
        }), 500
