"""Markdown formatting utilities for wikilinks and text."""

import re
from pathlib import Path
from typing import Literal, Optional


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
