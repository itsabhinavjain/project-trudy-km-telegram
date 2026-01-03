"""Media processor for images and documents."""

from pathlib import Path

from src.core.logger import get_logger
from src.markdown.formatter import format_wikilink
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.downloader import MediaDownloader
from src.telegram.fetcher import Message

logger = get_logger(__name__)


class MediaProcessor(BaseProcessor):
    """Processes image and document messages."""

    def __init__(self, config, downloader: MediaDownloader):
        """Initialize media processor.

        Args:
            config: Application configuration
            downloader: Media downloader instance
        """
        super().__init__(config)
        self.downloader = downloader

    async def can_process(self, message: Message) -> bool:
        """Check if this is an image or document message.

        Args:
            message: Message to check

        Returns:
            True if message is an image or document
        """
        return message.message_type in ["photo", "image", "document"]

    async def process(
        self,
        message: Message,
        media_dir: Path,
        notes_dir: Path,
    ) -> ProcessedResult:
        """Process an image or document message.

        Args:
            message: Message to process
            media_dir: Directory for media files
            notes_dir: Directory for notes

        Returns:
            Processed result with markdown content
        """
        logger.debug(f"Processing {message.message_type} message {message.message_id}")

        # Download media file
        media_file = await self.downloader.download_media(message, media_dir)

        if not media_file:
            logger.error(f"Failed to download media for message {message.message_id}")
            return ProcessedResult(
                markdown_content=f"**{message.message_type.capitalize()} - Download Failed**\n\n",
                metadata={"type": message.message_type, "error": "download_failed"},
            )

        # Determine header based on type
        if message.message_type in ["photo", "image"]:
            header = "Image"
        else:
            header = "Document"

        # Build markdown content
        content_parts = []
        content_parts.append(self._format_header(message, header))

        # Add wikilink with caption (if available)
        wikilink = format_wikilink(
            filename=media_file.name,
            caption=message.caption,
            style=self.config.markdown.wikilink_style,
            is_embed=(message.message_type in ["photo", "image"]),  # Embed images
        )
        content_parts.append(f"{wikilink}\n\n")

        # Add caption as separate text if present and not already in wikilink alt text
        # (for obsidian style, caption is in alt text, so we don't repeat it)
        if (
            message.caption
            and self.config.markdown.wikilink_style != "obsidian"
        ):
            content_parts.append(f"{message.caption}\n\n")

        markdown_content = "".join(content_parts)

        return ProcessedResult(
            markdown_content=markdown_content,
            media_files=[media_file],
            metadata={
                "type": message.message_type,
                "filename": media_file.name,
                "has_caption": message.caption is not None,
            },
        )
