"""Staging markdown writer for Phase 1 (Fetch to Staging)."""

import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.config import MarkdownConfig
from src.markdown.formatter import MarkdownFormatter


class StagingWriter:
    """Write messages to staging area in simple format.

    Staging format is designed to be simple and raw:
    - Verbatim text in headers for easy scanning
    - Minimal structure, no metadata
    - Human-readable timestamps
    - Direct media links
    """

    def __init__(self, config: MarkdownConfig):
        """Initialize staging writer.

        Args:
            config: Markdown configuration
        """
        self.config = config
        self.formatter = MarkdownFormatter(config)

    async def append_entry(
        self,
        staging_dir: Path,
        message,  # Message object
        media_path: Optional[Path] = None,
        caption: Optional[str] = None,
    ) -> Path:
        """Append message to staging file.

        Args:
            staging_dir: Staging directory for user
            message: Message object with timestamp, text, message_type
            media_path: Path to downloaded media file (if any)
            caption: Media caption (if any)

        Returns:
            Path to staging file that was written

        Format:
            ## HH:MM - <first 50 chars or [Media Type]>

            <content/media link>

            ---
        """
        # Determine daily file based on message timestamp
        date_str = self.formatter.format_date(message.timestamp)
        staging_file = staging_dir / f"{date_str}.md"

        # Ensure directory exists
        staging_dir.mkdir(parents=True, exist_ok=True)

        # Format header
        header = self._format_header(message)

        # Format content
        content = self._format_content(message, media_path, caption)

        # Build entry
        entry = f"{header}\n\n{content}\n\n---\n\n"

        # Append to file with locking
        with open(staging_file, "a", encoding="utf-8") as f:
            # Acquire exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(entry)
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return staging_file

    def _format_header(self, message) -> str:
        """Format header for staging entry.

        Args:
            message: Message object

        Returns:
            Formatted header string

        Examples:
            ## 14:30 - Hello, this is a test message
            ## 14:35 - [Image]
            ## 14:40 - [Video]
        """
        # Format timestamp
        time_str = self.formatter.format_time(message.timestamp)

        # Get preview text
        preview = self._get_preview_text(message)

        return f"## {time_str} - {preview}"

    def _get_preview_text(self, message) -> str:
        """Get preview text for header.

        Args:
            message: Message object

        Returns:
            Preview string (first 50 chars or media type indicator)
        """
        # For media messages, show media type
        if message.message_type in ["image", "photo", "video", "audio", "voice", "document", "video_note"]:
            type_map = {
                "image": "Image",
                "photo": "Image",
                "video": "Video",
                "video_note": "Video Note",
                "audio": "Audio",
                "voice": "Voice Message",
                "document": "Document",
            }
            return f"[{type_map.get(message.message_type, 'Media')}]"

        # For text messages with URLs (including YouTube)
        if message.text:
            # Check if it's primarily a link
            text_stripped = message.text.strip()
            if text_stripped.startswith("http://") or text_stripped.startswith("https://"):
                # If text is just a URL or starts with URL, truncate appropriately
                return self.formatter.sanitize_text(text_stripped, max_length=50)
            else:
                # Regular text message
                return self.formatter.sanitize_text(message.text, max_length=50)

        # For messages with caption only
        if message.caption:
            return self.formatter.sanitize_text(message.caption, max_length=50)

        return "[Empty Message]"

    def _format_content(
        self,
        message,
        media_path: Optional[Path],
        caption: Optional[str],
    ) -> str:
        """Format content section of staging entry.

        Args:
            message: Message object
            media_path: Path to media file (if any)
            caption: Media caption (if any)

        Returns:
            Formatted content string
        """
        content_parts = []

        # Handle media
        if media_path:
            content_parts.append(self._format_media_link(message.message_type, media_path))

            # Add caption if present
            if caption:
                content_parts.append(f"\nCaption: {caption}")

        # Handle text
        elif message.text:
            content_parts.append(message.text)

        # Handle caption-only (shouldn't happen but handle it)
        elif caption:
            content_parts.append(caption)

        return "\n\n".join(content_parts) if content_parts else ""

    def _format_media_link(self, message_type: str, media_path: Path) -> str:
        """Format media link for staging.

        Args:
            message_type: Type of media
            media_path: Path to media file

        Returns:
            Formatted markdown link
        """
        # Get relative path from staging file to media file
        # Staging file is at: data/staging/<user>/YYYY-MM-DD.md
        # Media file is at: data/media/<user>/filename.ext
        # Relative path: ../../media/<user>/filename.ext

        # For simplicity, use relative path pattern
        relative_path = f"../media/{media_path.parent.name}/{media_path.name}"

        # Format based on type
        if message_type in ["image", "photo"]:
            # Embedded image
            return f"![Image]({relative_path})"
        elif message_type in ["video", "video_note"]:
            # Video link
            return f"[Video]({relative_path})"
        elif message_type in ["audio", "voice"]:
            # Audio link
            return f"[Audio]({relative_path})"
        elif message_type == "document":
            # Document link
            filename = media_path.name
            return f"[{filename}]({relative_path})"
        else:
            # Generic media link
            return f"[Media]({relative_path})"
