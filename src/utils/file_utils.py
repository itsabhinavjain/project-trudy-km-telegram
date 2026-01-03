"""File utilities for filename sanitization and generation."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils.datetime_utils import format_timestamp_for_filename


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Sanitize filename for safe filesystem use.

    - Replaces spaces with hyphens
    - Removes special characters
    - Limits length
    - Preserves file extension

    Args:
        filename: Original filename
        max_length: Maximum filename length (excluding extension)

    Returns:
        Sanitized filename
    """
    # Split filename and extension
    path = Path(filename)
    name = path.stem
    ext = path.suffix

    # Replace spaces with hyphens
    name = name.replace(" ", "-")

    # Remove special characters (keep alphanumeric, hyphens, underscores)
    name = re.sub(r"[^a-zA-Z0-9\-_]", "", name)

    # Remove multiple consecutive hyphens
    name = re.sub(r"-+", "-", name)

    # Trim leading/trailing hyphens
    name = name.strip("-")

    # Fallback if name is empty
    if not name:
        name = "file"

    # Limit length
    if len(name) > max_length:
        name = name[:max_length].rstrip("-")

    return f"{name}{ext}"


def generate_media_filename(
    timestamp: datetime,
    media_type: str,
    original_filename: Optional[str] = None,
    extension: Optional[str] = None,
) -> str:
    """Generate filename for media file: YYYY-MM-DD_HH-MM-SS_filename.ext.

    Args:
        timestamp: Message timestamp
        media_type: Type of media (video, audio, image, photo, document)
        original_filename: Original filename from Telegram (if available)
        extension: File extension (if not in original_filename)

    Returns:
        Generated filename
    """
    # Format timestamp part
    timestamp_part = format_timestamp_for_filename(timestamp)

    # Determine name part
    if original_filename:
        sanitized = sanitize_filename(original_filename, max_length=50)
        # If sanitized filename has no extension and we have one, add it
        if not Path(sanitized).suffix and extension:
            name_part = f"{Path(sanitized).stem}{extension if extension.startswith('.') else '.' + extension}"
        else:
            name_part = sanitized
    else:
        # Use media type as fallback
        name_part = f"{media_type}{extension if extension and extension.startswith('.') else ''}"

    return f"{timestamp_part}_{name_part}"


def generate_transcript_filename(media_filename: str) -> str:
    """Generate transcript filename from media filename.

    Args:
        media_filename: Media filename (e.g., "2026-01-03_14-23-45_video.mp4")

    Returns:
        Transcript filename (e.g., "2026-01-03_14-23-45_video_transcript.txt")
    """
    path = Path(media_filename)
    return f"{path.stem}_transcript.txt"


def sanitize_youtube_title(title: str, max_length: int = 50) -> str:
    """Sanitize YouTube video title for use in filenames.

    Args:
        title: YouTube video title
        max_length: Maximum title length

    Returns:
        Sanitized title
    """
    # Replace spaces with hyphens
    title = title.replace(" ", "-")

    # Remove special characters
    title = re.sub(r"[^a-zA-Z0-9\-_]", "", title)

    # Remove multiple consecutive hyphens
    title = re.sub(r"-+", "-", title)

    # Trim leading/trailing hyphens
    title = title.strip("-")

    # Fallback if empty
    if not title:
        title = "YouTube-Video"

    # Limit length
    if len(title) > max_length:
        title = title[:max_length].rstrip("-")

    return title


def generate_youtube_transcript_filename(
    timestamp: datetime, video_title: str
) -> str:
    """Generate transcript filename for YouTube video.

    Args:
        timestamp: Message timestamp
        video_title: YouTube video title

    Returns:
        Transcript filename (e.g., "2026-01-03_15-10-22_How-to-Build-AI-Apps_transcript.txt")
    """
    timestamp_part = format_timestamp_for_filename(timestamp)
    sanitized_title = sanitize_youtube_title(video_title)

    return f"{timestamp_part}_{sanitized_title}_transcript.txt"


def ensure_directory_exists(directory: Path) -> None:
    """Ensure directory exists, creating it if necessary.

    Args:
        directory: Directory path to create
    """
    directory.mkdir(parents=True, exist_ok=True)


def get_unique_filename(directory: Path, filename: str) -> str:
    """Get unique filename by adding suffix if file exists.

    Args:
        directory: Directory where file will be saved
        filename: Desired filename

    Returns:
        Unique filename (may have _1, _2, etc. suffix)
    """
    path = directory / filename
    if not path.exists():
        return filename

    # File exists, find unique name
    base = Path(filename)
    stem = base.stem
    suffix = base.suffix

    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_filename
        counter += 1


def get_file_extension_from_mime(mime_type: str) -> str:
    """Get file extension from MIME type.

    Args:
        mime_type: MIME type string

    Returns:
        File extension (with dot)
    """
    mime_map = {
        # Video
        "video/mp4": ".mp4",
        "video/mpeg": ".mpeg",
        "video/quicktime": ".mov",
        "video/x-msvideo": ".avi",
        "video/webm": ".webm",
        # Audio
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "audio/webm": ".weba",
        "audio/aac": ".aac",
        # Image
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        # Document
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "text/plain": ".txt",
    }

    return mime_map.get(mime_type, "")
