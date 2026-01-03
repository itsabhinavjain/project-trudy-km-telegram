"""Markdown file writer for daily notes."""

import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles

from src.core.config import MarkdownConfig
from src.core.logger import get_logger
from src.telegram.fetcher import Message
from src.utils.datetime_utils import (
    format_date_for_filename,
    format_timestamp_for_header,
    to_local_datetime,
)
from src.utils.file_utils import ensure_directory_exists

logger = get_logger(__name__)


class MarkdownWriter:
    """Writes message entries to daily markdown files."""

    def __init__(self, config: MarkdownConfig):
        """Initialize markdown writer.

        Args:
            config: Markdown formatting configuration
        """
        self.config = config

    async def append_entry(
        self,
        notes_dir: Path,
        message: Message,
        content: str,
    ) -> Path:
        """Append an entry to the appropriate daily markdown file.

        Args:
            notes_dir: Directory containing note files
            message: Message being processed
            content: Markdown content to append

        Returns:
            Path to the markdown file that was written

        Raises:
            IOError: If file operation fails
        """
        # Ensure notes directory exists
        ensure_directory_exists(notes_dir)

        # Convert message timestamp to local timezone
        local_time = to_local_datetime(message.timestamp, self.config.timezone)

        # Get filename for this day
        date_str = format_date_for_filename(local_time)
        markdown_file = notes_dir / f"{date_str}.md"

        # Check if file exists and needs header
        file_exists = markdown_file.exists()

        # Format time header
        time_header = format_timestamp_for_header(
            message.timestamp,
            self.config.timezone,
            self.config.timestamp_format,
        )

        # Build entry content
        entry_parts = []

        # If new file, add date header
        if not file_exists:
            entry_parts.append(f"# {date_str}\n\n")

        # Add time header
        entry_parts.append(f"## {time_header}\n\n")

        # Add message ID comment if configured
        if self.config.include_message_id:
            entry_parts.append(f"<!-- message_id: {message.message_id} -->\n\n")

        # Add content
        entry_parts.append(content)

        # Add separator
        entry_parts.append("\n---\n\n")

        entry = "".join(entry_parts)

        # Write to file with locking for thread safety
        try:
            async with aiofiles.open(markdown_file, "a", encoding="utf-8") as f:
                # Acquire file lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    await f.write(entry)
                    await f.flush()
                finally:
                    # Release file lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            logger.debug(f"Appended entry to {markdown_file}")
            return markdown_file

        except Exception as e:
            logger.error(f"Failed to write to {markdown_file}: {e}")
            raise

    async def create_or_update_file(
        self,
        notes_dir: Path,
        filename: str,
        content: str,
        mode: str = "w",
    ) -> Path:
        """Create or update a file with content.

        Args:
            notes_dir: Directory for the file
            filename: Name of the file
            content: Content to write
            mode: File mode ('w' for overwrite, 'a' for append)

        Returns:
            Path to the file

        Raises:
            IOError: If file operation fails
        """
        ensure_directory_exists(notes_dir)
        file_path = notes_dir / filename

        try:
            async with aiofiles.open(file_path, mode, encoding="utf-8") as f:
                await f.write(content)

            logger.debug(f"Wrote to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to write to {file_path}: {e}")
            raise

    def get_daily_note_path(
        self,
        notes_dir: Path,
        date: Optional[datetime] = None,
    ) -> Path:
        """Get path to daily note file for a given date.

        Args:
            notes_dir: Directory containing note files
            date: Date for the note (defaults to today in configured timezone)

        Returns:
            Path to the daily note file
        """
        if date is None:
            from src.utils.datetime_utils import utcnow

            date = utcnow()

        local_time = to_local_datetime(date, self.config.timezone)
        date_str = format_date_for_filename(local_time)
        return notes_dir / f"{date_str}.md"
