"""Markdown formatting utilities for wikilinks and text."""

import re
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import pytz

from src.core.config import MarkdownConfig


def format_wikilink(
    filename: str,
    caption: Optional[str] = None,
    style: Literal["obsidian", "standard"] = "obsidian",
    is_embed: bool = True,
) -> str:
    """Format a wikilink to a file.

    Args:
        filename: Name of the file to link to
        caption: Optional caption/alt text
        style: Wikilink style (obsidian or standard)
        is_embed: If True, use embed syntax (![[...]]), else use link syntax ([[...]])

    Returns:
        Formatted wikilink
    """
    if style == "obsidian":
        # Obsidian style: ![[filename|caption]] or [[filename|caption]]
        prefix = "!" if is_embed else ""
        if caption:
            return f"{prefix}[[{filename}|{caption}]]"
        else:
            return f"{prefix}[[{filename}]]"
    else:
        # Standard markdown
        if is_embed:
            # For embeds, use image syntax
            return f"![{caption or ''}]({filename})"
        else:
            # For links, use link syntax
            return f"[{caption or filename}]({filename})"


def format_transcript_link(
    transcript_filename: str,
    style: Literal["obsidian", "standard"] = "obsidian",
) -> str:
    """Format a link to a transcript file.

    Args:
        transcript_filename: Name of the transcript file
        style: Wikilink style

    Returns:
        Formatted link
    """
    return f"**Transcript:** {format_wikilink(transcript_filename, style=style, is_embed=False)}\n\n"


def escape_markdown(text: str) -> str:
    """Escape special markdown characters in text.

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    # Escape special markdown characters
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def format_bullet_list(items: list[str]) -> str:
    """Format a list of items as markdown bullet points.

    Args:
        items: List of items

    Returns:
        Formatted bullet list
    """
    return "\n".join(f"- {item}" for item in items)


def format_url_link(url: str, title: Optional[str] = None) -> str:
    """Format a URL as a markdown link.

    Args:
        url: URL to link to
        title: Optional title text

    Returns:
        Formatted link
    """
    if title:
        return f"[{title}]({url})"
    else:
        return url


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text.

    Args:
        text: Text to extract URLs from

    Returns:
        List of URLs found
    """
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    return re.findall(url_pattern, text)


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube link.

    Args:
        url: URL to check

    Returns:
        True if URL is a YouTube link
    """
    youtube_patterns = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=",
        r"(?:https?://)?(?:www\.)?youtu\.be/",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/",
    ]
    return any(re.search(pattern, url) for pattern in youtube_patterns)


def format_code_block(code: str, language: str = "") -> str:
    """Format text as a code block.

    Args:
        code: Code to format
        language: Optional language identifier

    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```\n"


def format_blockquote(text: str) -> str:
    """Format text as a blockquote.

    Args:
        text: Text to quote

    Returns:
        Formatted blockquote
    """
    lines = text.split("\n")
    return "\n".join(f"> {line}" for line in lines)


def format_callout(
    title: str,
    content: str,
    callout_type: Literal["note", "info", "warning", "error", "success"] = "note",
) -> str:
    """Format an Obsidian-style callout.

    Args:
        title: Callout title
        content: Callout content
        callout_type: Type of callout

    Returns:
        Formatted callout (Obsidian format)
    """
    return f"> [!{callout_type}] {title}\n> {content}\n\n"


class MarkdownFormatter:
    """Markdown formatter with timezone and date/time formatting support."""

    def __init__(self, config: MarkdownConfig):
        """Initialize formatter.

        Args:
            config: Markdown configuration
        """
        self.config = config
        self.timezone = pytz.timezone(config.timezone)

    def format_time(self, timestamp: datetime) -> str:
        """Format timestamp as time string.

        Args:
            timestamp: Datetime to format

        Returns:
            Formatted time string (e.g., "14:30")
        """
        # Convert to configured timezone
        if timestamp.tzinfo is None:
            timestamp = pytz.utc.localize(timestamp)

        local_time = timestamp.astimezone(self.timezone)

        # Format using Python's strftime (convert from config format)
        # Config uses "HH:mm" but strftime uses "%H:%M"
        format_str = self.config.timestamp_format.replace("HH", "%H").replace("mm", "%M")

        return local_time.strftime(format_str)

    def format_date(self, timestamp: datetime) -> str:
        """Format timestamp as date string.

        Args:
            timestamp: Datetime to format

        Returns:
            Formatted date string (e.g., "2026-01-04")
        """
        # Convert to configured timezone
        if timestamp.tzinfo is None:
            timestamp = pytz.utc.localize(timestamp)

        local_time = timestamp.astimezone(self.timezone)

        # Format using Python's strftime (convert from config format)
        # Config uses "YYYY-MM-DD" but strftime uses "%Y-%m-%d"
        format_str = self.config.date_format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")

        return local_time.strftime(format_str)

    def format_datetime(self, timestamp: datetime) -> str:
        """Format timestamp as full datetime string.

        Args:
            timestamp: Datetime to format

        Returns:
            Formatted datetime string
        """
        return f"{self.format_date(timestamp)} {self.format_time(timestamp)}"

    def sanitize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize text for use in headers or previews.

        Args:
            text: Text to sanitize
            max_length: Optional maximum length to truncate to

        Returns:
            Sanitized text
        """
        # Replace newlines with spaces
        sanitized = text.replace("\n", " ").replace("\r", " ")

        # Collapse multiple spaces
        sanitized = re.sub(r"\s+", " ", sanitized)

        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()

        # Truncate if needed
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip() + "..."

        return sanitized

    def get_relative_media_path(self, media_path: Path, markdown_file: Path) -> str:
        """Get relative path from markdown file to media file.

        Args:
            media_path: Absolute or relative path to media file
            markdown_file: Path to markdown file

        Returns:
            Relative path string
        """
        try:
            # Try to calculate relative path
            relative = Path(media_path).relative_to(markdown_file.parent)
            return str(relative)
        except ValueError:
            # If paths don't share a common base, just use the media path
            return str(media_path)
