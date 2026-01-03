"""Base processor interface for message handling."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.telegram.fetcher import Message


@dataclass
class ProcessedResult:
    """Result of processing a message."""

    markdown_content: str
    media_files: List[Path] = None
    transcript_file: Optional[Path] = None
    summary: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.media_files is None:
            self.media_files = []
        if self.metadata is None:
            self.metadata = {}


class BaseProcessor(ABC):
    """Abstract base class for message processors."""

    def __init__(self, config):
        """Initialize processor.

        Args:
            config: Application configuration
        """
        self.config = config

    @abstractmethod
    async def can_process(self, message: Message) -> bool:
        """Check if this processor can handle the message.

        Args:
            message: Message to check

        Returns:
            True if processor can handle this message type
        """
        pass

    @abstractmethod
    async def process(
        self,
        message: Message,
        media_dir: Path,
        notes_dir: Path,
    ) -> ProcessedResult:
        """Process a message and return markdown content.

        Args:
            message: Message to process
            media_dir: Directory for media files
            notes_dir: Directory for note files

        Returns:
            Processed result with markdown content and metadata

        Raises:
            Exception: If processing fails
        """
        pass

    def _format_header(self, message: Message, title: str) -> str:
        """Format a section header for the markdown entry.

        Args:
            message: Message being processed
            title: Title for the section

        Returns:
            Formatted header string
        """
        return f"**{title}**\n\n"

    def _format_summary(self, summary: str) -> str:
        """Format a summary section.

        Args:
            summary: Summary text

        Returns:
            Formatted summary
        """
        return f"**Summary:**\n{summary}\n\n"

    def _format_separator(self) -> str:
        """Get section separator.

        Returns:
            Markdown separator
        """
        return "---\n\n"
