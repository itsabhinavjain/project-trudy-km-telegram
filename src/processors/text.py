"""Text message processor."""

from pathlib import Path

from src.core.logger import get_logger
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.fetcher import Message

logger = get_logger(__name__)


class TextProcessor(BaseProcessor):
    """Processes plain text messages."""

    async def can_process(self, message: Message) -> bool:
        """Check if this is a plain text message (not a link).

        Args:
            message: Message to check

        Returns:
            True if message is plain text
        """
        return message.message_type == "text" and message.text is not None

    async def process(
        self,
        message: Message,
        media_dir: Path,
        notes_dir: Path,
    ) -> ProcessedResult:
        """Process a text message.

        Args:
            message: Message to process
            media_dir: Directory for media files (unused)
            notes_dir: Directory for notes (unused)

        Returns:
            Processed result with markdown content
        """
        logger.debug(f"Processing text message {message.message_id}")

        # Simple text message - just include the text
        markdown_content = f"{message.text}\n\n"

        return ProcessedResult(
            markdown_content=markdown_content,
            metadata={"type": "text"},
        )
