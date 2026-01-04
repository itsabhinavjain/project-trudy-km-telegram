"""Staging markdown reader for Phase 2 (Staging to Processing)."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

import pytz

from src.core.config import MarkdownConfig
from src.telegram.fetcher import Message


class StagingReader:
    """Parse staging markdown files into Message objects.

    Staging format is simple:
    ## HH:MM - <preview text>

    <content>

    ---
    """

    def __init__(self, config: MarkdownConfig):
        """Initialize staging reader.

        Args:
            config: Markdown configuration
        """
        self.config = config
        self.timezone = pytz.timezone(config.timezone)

    async def read_file(self, filepath: Path, username: str) -> List[Message]:
        """Parse staging markdown file into Message objects.

        Args:
            filepath: Path to staging file
            username: Username (for reconstructing Message objects)

        Returns:
            List of Message objects
        """
        if not filepath.exists():
            return []

        # Extract date from filename (YYYY-MM-DD.md)
        date_str = filepath.stem  # e.g., "2026-01-04"

        # Read file content
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by entry separator (---)
        entries = content.split("\n---\n")

        messages = []
        for i, entry in enumerate(entries):
            entry = entry.strip()
            if not entry:
                continue

            try:
                message = self._parse_entry(entry, date_str, username, i)
                if message:
                    messages.append(message)
            except Exception as e:
                # Log but continue with other entries
                print(f"Warning: Failed to parse entry {i} in {filepath}: {e}")
                continue

        return messages

    def _parse_entry(
        self,
        entry: str,
        date_str: str,
        username: str,
        entry_index: int,
    ) -> Optional[Message]:
        """Parse single entry into Message object.

        Args:
            entry: Entry text
            date_str: Date string (YYYY-MM-DD)
            username: Username
            entry_index: Index of entry in file

        Returns:
            Message object or None if parsing fails
        """
        # Parse header: ## HH:MM - <preview>
        lines = entry.split("\n", 1)
        if not lines:
            return None

        header = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        # Extract time from header
        # Format: ## 14:30 - Preview text
        header_match = re.match(r"##\s+(\d{1,2}:\d{2})\s+-\s+(.+)", header)
        if not header_match:
            return None

        time_str = header_match.group(1)
        preview = header_match.group(2)

        # Parse timestamp
        timestamp = self._parse_timestamp(date_str, time_str)

        # Determine message type and extract content
        message_type, text, caption, file_id = self._parse_content(preview, content)

        # Create synthetic message ID (since we don't store it in staging)
        # Use timestamp + entry index to create a unique-ish ID
        message_id = int(timestamp.timestamp() * 1000) + entry_index

        return Message(
            message_id=message_id,
            chat_id=0,  # Not available from staging
            user_id=0,  # Not available from staging
            username=username,
            timestamp=timestamp,
            message_type=message_type,
            text=text,
            caption=caption,
            file_id=file_id,  # Marker to indicate media exists
            file_name=None,
            file_size=None,
            mime_type=None,
        )

    def _parse_timestamp(self, date_str: str, time_str: str) -> datetime:
        """Parse date and time into datetime object.

        Args:
            date_str: Date string (YYYY-MM-DD)
            time_str: Time string (HH:MM)

        Returns:
            Datetime object
        """
        # Combine date and time
        datetime_str = f"{date_str} {time_str}"

        # Parse
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

        # Localize to configured timezone
        dt = self.timezone.localize(dt)

        return dt

    def _parse_content(
        self,
        preview: str,
        content: str,
    ) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
        """Parse content to determine message type and extract data.

        Args:
            preview: Preview text from header
            content: Content section

        Returns:
            Tuple of (message_type, text, caption, file_id_marker)
        """
        # Check if preview indicates media type
        media_indicators = {
            "[Image]": "image",
            "[Video]": "video",
            "[Video Note]": "video_note",
            "[Audio]": "audio",
            "[Voice Message]": "voice",
            "[Document]": "document",
        }

        for indicator, msg_type in media_indicators.items():
            if preview.startswith(indicator):
                # It's a media message
                # Extract caption if present
                caption = None
                if "Caption:" in content:
                    caption_match = re.search(r"Caption:\s*(.+?)(?:\n|$)", content, re.DOTALL)
                    if caption_match:
                        caption = caption_match.group(1).strip()

                # Use content line as marker that media exists
                file_id = "STAGING_MEDIA"  # Marker value
                return (msg_type, None, caption, file_id)

        # Not a media indicator, check content for media links
        # Look for ![Image](...) or [Video](...) etc.
        if re.search(r"!\[.*?\]\(.*?\)", content):
            # Embedded image
            caption = None
            if "Caption:" in content:
                caption_match = re.search(r"Caption:\s*(.+?)(?:\n|$)", content, re.DOTALL)
                if caption_match:
                    caption = caption_match.group(1).strip()
            return ("image", None, caption, "STAGING_MEDIA")

        if re.search(r"\[Video\]\(.*?\)", content):
            caption = None
            if "Caption:" in content:
                caption_match = re.search(r"Caption:\s*(.+?)(?:\n|$)", content, re.DOTALL)
                if caption_match:
                    caption = caption_match.group(1).strip()
            return ("video", None, caption, "STAGING_MEDIA")

        if re.search(r"\[Audio\]\(.*?\)", content):
            return ("audio", None, None, "STAGING_MEDIA")

        if re.search(r"\[.*?\]\(.*?\.pdf\)", content, re.IGNORECASE):
            return ("document", None, None, "STAGING_MEDIA")

        # Check for YouTube or other links
        if "http://" in content or "https://" in content:
            return ("link", content, None, None)

        # Default: text message
        return ("text", content, None, None)
