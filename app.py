"""
app.py — Entry point for the Termux Media Server.

Usage:
    python app.py                  # start the server
    python app.py --cleanup-cache  # remove incomplete cache entries, then exit
    python app.py --clear-cache    # remove ALL cache, then exit
    python app.py --port 9090      # use a custom port
"""

import os
import sys
import socket
import shutil
import argparse
import logging

# ============================================================
# LOGGING — configure before importing anything else
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("media-server")

# ============================================================
# IMPORTS (after logging is configured)
# ============================================================

import config


# ============================================================
# UTILITY
# ============================================================

def get_local_ip() -> str:
    """
    Best-effort detection of the local LAN IP.
    Works on Android/Termux and standard Linux.
    Falls back to 127.0.0.1 if detection fails.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        return ip
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


# ============================================================
# STARTUP CHECKS
# ============================================================

def startup_checks() -> bool:
    """
    Verify all required components before starting.
    Returns True if everything is ready, False if something is wrong
    (the server will still attempt to start but warn the user).
    """
    from transcoding.ffmpeg import check_available

    all_ok = True

    print()
    print("=" * 44)
    print("         TERMUX MEDIA SERVER")
    print("=" * 44)
    print()

    # ---- Media root ----
    print(f"  Media root:  {config.MEDIA_ROOT}")
    if os.path.isdir(config.MEDIA_ROOT):
        if os.access(config.MEDIA_ROOT, os.R_OK):
            print("               \u2713 Accessible")
        else:
            print("               \u2717 NOT READABLE")
            print("               Fix: check storage permissions")
            all_ok = False
    else:
        print("               \u2717 NOT FOUND")
        print("               Fix: create the directory or set the")
        print("               MEDIA_ROOT environment variable")
        all_ok = False

    print()

    # ---- FFmpeg / FFprobe ----
    ffmpeg_ok, ffprobe_ok = check_available()

    print(f"  FFmpeg:      {'✓ Found' if ffmpeg_ok else '✗ NOT FOUND'}")
    if not ffmpeg_ok:
        print("               Fix: pkg install ffmpeg")
        all_ok = False

    print(f"  FFprobe:     {'✓ Found' if ffprobe_ok else '✗ NOT FOUND'}")
    if not ffprobe_ok:
        print("               Fix: pkg install ffmpeg")
        all_ok = False

    print()

    # ---- HLS.js ----
    print(f"  HLS.js:      {'✓ Found' if os.path.isfile(config.HLS_JS_PATH) else '✗ NOT FOUND'}")
    if not os.path.isfile(config.HLS_JS_PATH):
        print(f"               Expected: {config.HLS_JS_PATH}")
        print("               Fix: see README.md \u2192 Installation \u2192 HLS.js")
        all_ok = False

    print()

    # ---- Cache + log directories ----
    try:
        os.makedirs(config.HLS_CACHE_DIR, exist_ok=True)
        os.makedirs(config.METADATA_CACHE_DIR, exist_ok=True)
        os.makedirs(config.LOG_DIR, exist_ok=True)
        print(f"  Cache:       \u2713 {config.CACHE_DIR}")
    except OSError as exc:
        print(f"  Cache:       \u2717 Cannot create: {exc}")
        all_ok = False

    print()
    return all_ok


# ============================================================
# CACHE MANAGEMENT
# ============================================================

def cleanup_cache(full: bool = False) -> None:
    """
    Remove cache entries.

    full=False → remove only entries that have no stream.m3u8
                 (incomplete / failed transcodes)
    full=True  → remove everything under HLS_CACHE_DIR
    """
    hls_dir = config.HLS_CACHE_DIR
    if not os.path.isdir(hls_dir):
        print("HLS cache directory does not exist — nothing to clean.")
        return

    removed = 0
    freed   = 0

    for name in os.listdir(hls_dir):
        job_dir  = os.path.join(hls_dir, name)
        if not os.path.isdir(job_dir):
            continue

        playlist = os.path.join(job_dir, "stream.m3u8")
        remove   = full or not os.path.exists(playlist)

        if remove:
            # Measure size before deleting
            for root, _dirs, fnames in os.walk(job_dir):
                for fname in fnames:
                    try:
                        freed += os.path.getsize(os.path.join(root, fname))
                    except OSError:
                        pass

            shutil.rmtree(job_dir, ignore_errors=True)
            removed += 1
            logger.info("Removed cache entry: %s", name)

    mb = freed // (1024 * 1024)
    print(f"Removed {removed} cache {'entries' if removed != 1 else 'entry'} "
          f"({mb} MB freed).")


# ============================================================
# FLASK APP FACTORY
# ============================================================

def create_app():
    from flask import Flask, redirect, url_for
    from routes.browse   import browse_bp
    from routes.playback import playback_bp
    from routes.api      import api_bp
    from routes.upload   import upload_bp
    from routes.delete   import delete_bp
    from routes.folder   import folder_bp
    from routes.rename   import rename_bp
    from routes.favorites import favorites_bp
    from routes.system_info import system_info_bp

    _base = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(_base, "templates"),
        static_folder=os.path.join(_base, "static"),
    )
    
    # Set max upload size
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_SIZE

    app.register_blueprint(browse_bp)
    app.register_blueprint(playback_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(delete_bp)
    app.register_blueprint(folder_bp)
    app.register_blueprint(rename_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(system_info_bp)

    # ---- Catch-all: redirect unknown URLs to the browser ----
    @app.errorhandler(404)
    def not_found(e):
        return redirect(url_for("browse.browse"), 302)

    return app



# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Termux Media Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python app.py\n"
            "  python app.py --port 9090\n"
            "  python app.py --cleanup-cache\n"
            "  python app.py --clear-cache\n"
            "  MEDIA_ROOT=/mnt/usb/Movies python app.py\n"
        ),
    )
    parser.add_argument(
        "--cleanup-cache",
        action="store_true",
        help="Remove incomplete/failed cache entries and exit",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Remove ALL transcoded cache entries and exit",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.PORT,
        help=f"Port to listen on (default: {config.PORT})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Flask debug mode (do not use in production)",
    )

    args = parser.parse_args()

    # ---- Cache management commands ----
    if args.cleanup_cache:
        cleanup_cache(full=False)
        sys.exit(0)

    if args.clear_cache:
        answer = input(
            f"\nThis will delete ALL transcoded videos in:\n"
            f"  {config.HLS_CACHE_DIR}\n\n"
            f"Original media will NOT be touched.\n"
            f"Continue? [y/N]: "
        ).strip().lower()
        if answer == "y":
            cleanup_cache(full=True)
        else:
            print("Cancelled.")
        sys.exit(0)

    # ---- Startup checks ----
    ok = startup_checks()
    
    # ---- Quick cleanup on startup (incomplete jobs only) ----
    # Full cache clear would scan all files, too slow on mobile
    logger.info("Cleaning up incomplete transcode jobs...")
    cleanup_cache(full=False)

    local_ip = get_local_ip()
    url      = f"http://{local_ip}:{args.port}"

    print(f"  Server:      {url}")
    print(f"  Max jobs:    {config.MAX_TRANSCODES}")
    print()
    print("  Open the URL above in your browser.")
    print("  Press CTRL+C to stop the server.")
    print()

    if not ok:
        print("  \u26a0  Some startup checks failed.")
        print("     See the messages above and consult README.md.")
        print()

    print("=" * 44)
    print()

    # ---- Start server ----
    app = create_app()

    app.run(
        host=config.HOST,
        port=args.port,
        debug=args.debug or config.DEBUG,
        threaded=True,
        use_reloader=False,   # reloader breaks background threads
    )


if __name__ == "__main__":
    main()
