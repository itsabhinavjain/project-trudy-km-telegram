"""Media processor for images and documents."""

from pathlib import Path
from typing import Optional

from src.ai.ocr import OCRManager
from src.core.logger import get_logger
from src.markdown.formatter import format_wikilink
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.downloader import MediaDownloader
from src.telegram.fetcher import Message

logger = get_logger(__name__)


class MediaProcessor(BaseProcessor):
    """Processes image and document messages.

    In v2.0: Media is already downloaded during fetch phase, so this processor
    focuses on finding existing media files and running OCR on images.
    """

    def __init__(
        self,
        config,
        downloader: MediaDownloader,
        ocr_manager: Optional[OCRManager] = None,
    ):
        """Initialize media processor.

        Args:
            config: Application configuration
            downloader: Media downloader instance (kept for backward compatibility)
            ocr_manager: Optional OCR manager for text extraction from images
        """
        super().__init__(config)
        self.downloader = downloader
        self.ocr_manager = ocr_manager

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

        In v2.0: Media should already be downloaded by fetcher. This method finds
        the media file and optionally runs OCR on images.

        Args:
            message: Message to process
            media_dir: Directory for media files
            notes_dir: Directory for notes

        Returns:
            Processed result with markdown content and OCR text (if applicable)
        """
        logger.debug(f"Processing {message.message_type} message {message.message_id}")

        # In v2.0, media should already exist. Try to find it first.
        # Media files follow pattern: YYYY-MM-DD_HH-MM-SS_<type>.<ext>
        # Since we don't know exact filename, look for files matching the timestamp
        media_file = None

        # Try to find existing media file by searching media_dir
        # In v2.0 staging workflow, the file_id or file_name from message might help
        if message.file_name:
            # Check if file exists with exact name
            potential_file = media_dir / message.file_name
            if potential_file.exists():
                media_file = potential_file

        # If not found by exact name, download it (backward compatibility for v1.x)
        if not media_file:
            logger.debug(f"Media file not found, downloading for message {message.message_id}")
            media_file = await self.downloader.download_media(message, media_dir)

        if not media_file:
            logger.error(f"Failed to find or download media for message {message.message_id}")
            return ProcessedResult(
                markdown_content=f"**{message.message_type.capitalize()} - Not Found**\n\n",
                message_type=message.message_type,
                metadata={"error": "media_not_found"},
            )

        # Determine header based on type
        if message.message_type in ["photo", "image"]:
            header = "Image"
        else:
            header = "Document"

        # Run OCR on images (if enabled)
        ocr_text = None
        if message.message_type in ["photo", "image"] and self.ocr_manager:
            logger.debug(f"Running OCR on {media_file.name}")
            ocr_text = await self.ocr_manager.extract_text(media_file)
            if ocr_text:
                logger.info(f"Extracted {len(ocr_text)} characters via OCR from {media_file.name}")

        # Build markdown content (for backward compatibility)
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

        # Add caption as separate text if present
        if message.caption and self.config.markdown.wikilink_style != "obsidian":
            content_parts.append(f"{message.caption}\n\n")

        # Add OCR text if extracted
        if ocr_text:
            content_parts.append(f"**OCR Text:**\n{ocr_text}\n\n")

        markdown_content = "".join(content_parts)

        return ProcessedResult(
            markdown_content=markdown_content,
            message_type=message.message_type,
            media_files=[media_file],
            ocr_text=ocr_text,
            reply_to=message.reply_to,  # v2.0: Preserve context
            forwarded_from=message.forwarded_from,  # v2.0: Preserve context
            edited_at=message.edited_at,  # v2.0: Preserve context
            metadata={
                "filename": media_file.name,
                "has_caption": message.caption is not None,
                "has_ocr": ocr_text is not None,
            },
        )
