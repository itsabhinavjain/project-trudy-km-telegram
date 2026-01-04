"""Media file downloader for Telegram attachments."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.core.logger import get_logger
from src.telegram.client import TelegramClient
from src.utils.file_utils import (
    ensure_directory_exists,
    generate_media_filename,
    get_file_extension_from_mime,
    get_unique_filename,
)

# Avoid circular import
if TYPE_CHECKING:
    from src.telegram.fetcher import Message

logger = get_logger(__name__)


class MediaDownloader:
    """Downloads media files from Telegram."""

    def __init__(self, client: TelegramClient):
        """Initialize media downloader.

        Args:
            client: Telegram client for downloading files
        """
        self.client = client

    async def download_media(
        self,
        message: "Message",
        media_dir: Path,
    ) -> Optional[Path]:
        """Download media file from a message.

        Args:
            message: Message containing media
            media_dir: Directory to save media files

        Returns:
            Path to downloaded file, or None if download failed
        """
        if not message.file_id:
            logger.warning(f"Message {message.message_id} has no file_id")
            return None

        try:
            # Ensure media directory exists
            ensure_directory_exists(media_dir)

            # Determine file extension
            extension = None
            if message.file_name:
                extension = Path(message.file_name).suffix
            elif message.mime_type:
                extension = get_file_extension_from_mime(message.mime_type)
            else:
                # Default extensions by type
                extension_map = {
                    "video": ".mp4",
                    "audio": ".mp3",
                    "voice": ".ogg",
                    "photo": ".jpg",
                    "image": ".jpg",
                    "document": ".pdf",
                }
                extension = extension_map.get(message.message_type, "")

            # Generate filename
            filename = generate_media_filename(
                timestamp=message.timestamp,
                media_type=message.message_type,
                original_filename=message.file_name,
                extension=extension,
            )

            # Ensure unique filename
            unique_filename = get_unique_filename(media_dir, filename)
            destination = media_dir / unique_filename

            # Check if file already exists (idempotency)
            if destination.exists():
                logger.info(f"File already exists: {unique_filename}")
                return destination

            # Get file path from Telegram
            logger.info(f"Downloading {message.message_type}: {unique_filename}")
            file_path = await self.client.get_file(message.file_id)

            # Download file
            await self.client.download_file(str(file_path), str(destination))

            logger.info(f"Downloaded to: {destination}")
            return destination

        except Exception as e:
            logger.error(
                f"Failed to download media from message {message.message_id}: {e}"
            )
            return None

    async def download_batch(
        self,
        messages: list["Message"],
        media_dir: Path,
    ) -> dict[int, Optional[Path]]:
        """Download media files from multiple messages.

        Args:
            messages: List of messages with media
            media_dir: Directory to save media files

        Returns:
            Dictionary mapping message_id to downloaded file path (or None if failed)
        """
        results = {}

        for message in messages:
            if message.file_id:
                path = await self.download_media(message, media_dir)
                results[message.message_id] = path
            else:
                results[message.message_id] = None

        return results
