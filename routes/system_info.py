"""
routes/system_info.py - System information and statistics endpoint
"""

import os
import platform
import logging
from flask import Blueprint, jsonify
import config

system_info_bp = Blueprint('system_info', __name__)
logger = logging.getLogger("media-server")

# Try to import psutil, make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("psutil loaded successfully")
    # Initialize CPU measurement on module load so first call has data
    psutil.cpu_percent(interval=None)
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system stats will be disabled")


@system_info_bp.route("/api/system-info")
def get_system_info():
    """
    Return system information: CPU, RAM, storage, platform.
    Falls back to basic info if psutil is not available.
    """
    try:
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available, returning placeholder data")
            # Fallback: basic info without psutil
            response = {
                "cpu": {"usage_percent": 0, "cores": 0, "frequency_mhz": None},
                "memory": {"total_mb": 0, "used_mb": 0, "available_mb": 0, "percent": 0},
                "storage": {
                    "media_root": {
                        "path": config.MEDIA_ROOT,
                        "total_gb": 0,
                        "used_gb": 0,
                        "free_gb": 0,
                        "percent": 0,
                    }
                },
                "cache": {"total_mb": 0, "used_mb": 0, "free_mb": 0},
                "system": {
                    "platform": platform.system(),
                    "platform_release": platform.release(),
                    "architecture": platform.machine(),
                    "hostname": platform.node(),
                    "python_version": platform.python_version(),
                },
                "uptime_hours": 0,
                "active_transcodes": 0,
                "psutil_available": False,
                "message": "Install psutil: pkg install python-psutil"
            }
            return jsonify(response)
        
        # Full stats with psutil
        logger.debug("Fetching system stats with psutil")
        
        # CPU Information
        try:
            # Use interval=None for non-blocking call (uses data since last call)
            # The module initialization already started the measurement
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # If first reading is 0, do a quick blocking call
            if cpu_percent == 0.0 or cpu_percent == 0:
                cpu_percent = psutil.cpu_percent(interval=0.1)
            
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            cpu_percent = 0
            cpu_count = 0
            cpu_freq = None
        
        # Memory Information
        try:
            memory = psutil.virtual_memory()
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            memory = type('obj', (object,), {
                'total': 0, 'used': 0, 'available': 0, 'percent': 0
            })()
        
        # Storage Information (media root)
        try:
            storage = psutil.disk_usage(config.MEDIA_ROOT)
        except Exception as e:
            logger.error(f"Error getting storage info for {config.MEDIA_ROOT}: {e}")
            storage = type('obj', (object,), {
                'total': 0, 'used': 0, 'free': 0, 'percent': 0
            })()
        
        # Cache storage
        try:
            cache_storage = psutil.disk_usage(config.CACHE_DIR)
        except Exception as e:
            logger.debug(f"Cache storage not available: {e}")
            cache_storage = None
        
        # System uptime
        try:
            boot_time = psutil.boot_time()
            from datetime import datetime
            uptime_seconds = datetime.now().timestamp() - boot_time
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            uptime_seconds = 0
        
        # Platform info
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
        }
        
        # Active transcoding jobs
        try:
            from transcoding.manager import manager
            active_jobs = len(manager._registry)
        except Exception as e:
            logger.error(f"Error getting active jobs: {e}")
            active_jobs = 0
        
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
            "psutil_available": True,
        }
        
        logger.debug(f"System stats: CPU {cpu_percent}%, RAM {memory.percent}%, Storage {storage.percent}%")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"System info endpoint error: {e}", exc_info=True)
        return jsonify({
            "error": str(e), 
            "psutil_available": PSUTIL_AVAILABLE,
            "message": "Error fetching system info. Check server logs."
        }), 500
