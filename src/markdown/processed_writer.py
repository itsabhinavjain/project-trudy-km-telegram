"""Processed markdown writer for Phase 2 (Staging to Processing).

Writes messages to processed area with rich YAML metadata format.
"""

import fcntl
from pathlib import Path
from typing import Optional

from src.core.config import MarkdownConfig
from src.markdown.formatter import MarkdownFormatter, format_wikilink
from src.processors.base import ProcessedResult


class ProcessedWriter:
    """Write messages to processed area in rich YAML format.

    Processed format includes:
    - Same header as staging for consistency
    - YAML-style metadata block with all enrichments
    - Wikilinks for media files
    - Full content with all processing results
    """

    def __init__(self, config: MarkdownConfig):
        """Initialize processed writer.

        Args:
            config: Markdown configuration
        """
        self.config = config
        self.formatter = MarkdownFormatter(config)

    async def append_entry(
        self,
        processed_dir: Path,
        message,  # Message object
        processed_result: ProcessedResult,
    ) -> Path:
        """Append processed message with rich metadata to processed file.

        Args:
            processed_dir: Processed directory for user
            message: Message object with timestamp, text, etc.
            processed_result: Processing results with metadata

        Returns:
            Path to processed file that was written

        Format:
            ## HH:MM - <preview>
            type: <message_type>
            <YAML metadata block>

            ---
        """
        # Determine daily file based on message timestamp
        date_str = self.formatter.format_date(message.timestamp)
        processed_file = processed_dir / f"{date_str}.md"

        # Ensure directory exists
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Format header (same as staging for consistency)
        header = self._format_header(message)

        # Format YAML metadata block
        metadata = self._format_metadata(message, processed_result)

        # Build entry
        entry = f"{header}\n{metadata}\n---\n\n"

        # Append to file with locking
        with open(processed_file, "a", encoding="utf-8") as f:
            # Acquire exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(entry)
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return processed_file

    def _format_header(self, message) -> str:
        """Format header for processed entry.

        Args:
            message: Message object

        Returns:
            Formatted header string (same format as staging)

        Examples:
            ## 14:30 - Hello, this is a test message
            ## 14:35 - [Image]
            ## 14:40 - [Video]
        """
        # Format timestamp
        time_str = self.formatter.format_time(message.timestamp)

        # Get preview text (same logic as staging)
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

        # For text messages with URLs
        if message.text:
            text_stripped = message.text.strip()
            if text_stripped.startswith("http://") or text_stripped.startswith("https://"):
                return self.formatter.sanitize_text(text_stripped, max_length=50)
            else:
                return self.formatter.sanitize_text(message.text, max_length=50)

        # For messages with caption only
        if message.caption:
            return self.formatter.sanitize_text(message.caption, max_length=50)

        return "[Empty Message]"

    def _format_metadata(
        self,
        message,
        result: ProcessedResult,
    ) -> str:
        """Format YAML-style metadata block.

        Args:
            message: Message object
            result: ProcessedResult with all metadata

        Returns:
            Formatted YAML metadata string
        """
        lines = []

        # Type field (always present)
        lines.append(f"type: {result.message_type}")

        # Content (for text messages)
        if message.text and result.message_type in ["text", "link"]:
            lines.append("content: |-")
            for line in message.text.split("\n"):
                lines.append(f"  {line}")

        # Media file (for media messages)
        if result.media_files:
            for media_file in result.media_files:
                wikilink = format_wikilink(
                    filename=media_file.name,
                    style=self.config.wikilink_style,
                    is_embed=True,
                )
                lines.append(f"file: {wikilink}")

        # Caption (for media with caption)
        if message.caption:
            lines.append("caption: |-")
            for line in message.caption.split("\n"):
                lines.append(f"  {line}")

        # Transcript file
        if result.transcript_file:
            wikilink = format_wikilink(
                filename=result.transcript_file.name,
                style=self.config.wikilink_style,
                is_embed=False,
            )
            lines.append(f"transcript: {wikilink}")

        # Summary
        if result.summary:
            lines.append("summary: |-")
            for line in result.summary.split("\n"):
                lines.append(f"  {line}")

        # OCR text
        if result.ocr_text:
            lines.append("ocr_text: |-")
            for line in result.ocr_text.split("\n"):
                lines.append(f"  {line}")

        # Tags
        if result.tags:
            tags_str = ", ".join(result.tags)
            lines.append(f"tags: [{tags_str}]")

        # Links (extracted metadata)
        if result.links:
            lines.append("links:")
            for link in result.links:
                lines.append(f"  - url: \"{link.get('url', '')}\"")
                if link.get('title'):
                    lines.append(f"    title: \"{link['title']}\"")
                if link.get('description'):
                    lines.append(f"    description: \"{link['description']}\"")

        # Reply context
        if result.reply_to:
            lines.append("reply_to:")
            lines.append(f"  message_id: {result.reply_to.get('message_id', '')}")
            if result.reply_to.get('timestamp'):
                lines.append(f"  timestamp: \"{result.reply_to['timestamp']}\"")
            if result.reply_to.get('preview'):
                lines.append(f"  preview: \"{result.reply_to['preview']}\"")

        # Forward context
        if result.forwarded_from:
            lines.append("forwarded_from:")
            lines.append(f"  user: \"{result.forwarded_from.get('user', '')}\"")
            if result.forwarded_from.get('chat_id'):
                lines.append(f"  chat_id: {result.forwarded_from['chat_id']}")
            if result.forwarded_from.get('original_date'):
                lines.append(f"  original_date: \"{result.forwarded_from['original_date']}\"")

        # Edit timestamp
        if result.edited_at:
            lines.append(f"edited_at: \"{result.edited_at.isoformat()}\"")

        # Message ID (if configured)
        if self.config.include_message_id:
            lines.append(f"message_id: {message.message_id}")

        # Additional metadata from processors
        if result.metadata:
            for key, value in result.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    lines.append(f"{key}: {value}")
                elif isinstance(value, list):
                    lines.append(f"{key}: {value}")
                elif isinstance(value, dict):
                    lines.append(f"{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")

        return "\n".join(lines)
