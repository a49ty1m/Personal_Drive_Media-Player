"""
media/scanner.py

Thin wrappers around filesystem.list_directory().
On-demand scanning (per request) means new files are visible
immediately without restarting the server.
"""

import os
from typing import List, Tuple

import config
from media.filesystem import list_directory
from media.models import Folder, MediaFile


def scan_directory(abs_path: str) -> Tuple[List[Folder], List[MediaFile]]:
    """
    Scan a single directory level.
    Returns (folders, media_files) — no recursion.
    Suitable for the browse route where users navigate folder by folder.
    """
    return list_directory(abs_path)


def scan_all() -> List[MediaFile]:
    """
    Recursively scan the entire MEDIA_ROOT and return a flat list of
    all MediaFile objects.

    Not used in Phase 1, but available for future indexing/search.
    """
    results: List[MediaFile] = []

    for dirpath, dirnames, filenames in os.walk(config.MEDIA_ROOT):
        # Skip hidden directories in-place (modifying dirnames affects os.walk)
        dirnames[:] = sorted(
            [d for d in dirnames if not d.startswith(".")],
            key=str.casefold
        )

        for name in sorted(filenames, key=str.casefold):
            if name.startswith("."):
                continue

            _, ext = os.path.splitext(name)
            if ext.lower() not in config.VIDEO_EXTENSIONS:
                continue

            full = os.path.join(dirpath, name)
            relative = (
                os.path.relpath(full, config.MEDIA_ROOT)
                .replace(os.sep, "/")
            )

            results.append(
                MediaFile(name=name, relative=relative, extension=ext.lower())
            )

    return results
