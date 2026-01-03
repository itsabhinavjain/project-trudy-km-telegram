"""Telegram Bot API client wrapper."""

import asyncio
from typing import List, Optional

from telegram import Bot, Update
from telegram.error import TelegramError, TimedOut, NetworkError

from src.core.config import TelegramConfig
from src.core.logger import get_logger

logger = get_logger(__name__)


class TelegramClient:
    """Wrapper around python-telegram-bot for Bot API operations."""

    def __init__(self, config: TelegramConfig):
        """Initialize Telegram client.

        Args:
            config: Telegram configuration
        """
        self.config = config
        self.bot = Bot(token=config.bot_token)
        self._request_semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

    async def get_me(self) -> dict:
        """Get information about the bot.

        Returns:
            Bot information

        Raises:
            TelegramError: If request fails
        """
        try:
            bot_info = await self.bot.get_me()
            return {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
            }
        except TelegramError as e:
            logger.error(f"Failed to get bot info: {e}")
            raise

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 0,
    ) -> List[Update]:
        """Get updates (messages) from Telegram.

        Args:
            offset: Identifier of the first update to be returned
            limit: Number of updates to retrieve (1-100)
            timeout: Long polling timeout in seconds

        Returns:
            List of Update objects

        Raises:
            TelegramError: If request fails
        """
        async with self._request_semaphore:
            try:
                updates = await self.bot.get_updates(
                    offset=offset,
                    limit=limit,
                    timeout=timeout,
                    allowed_updates=Update.ALL_TYPES,
                )
                return updates
            except (TimedOut, NetworkError) as e:
                logger.warning(f"Network error getting updates: {e}")
                return []
            except TelegramError as e:
                logger.error(f"Failed to get updates: {e}")
                raise

    async def get_file(self, file_id: str) -> str:
        """Get file path for downloading.

        Args:
            file_id: Telegram file ID

        Returns:
            File path URL for download

        Raises:
            TelegramError: If request fails
        """
        async with self._request_semaphore:
            try:
                file = await self.bot.get_file(file_id)
                return file.file_path
            except TelegramError as e:
                logger.error(f"Failed to get file {file_id}: {e}")
                raise

    async def download_file(self, file_path: str, destination: str) -> None:
        """Download file from Telegram servers.

        Args:
            file_path: File path from get_file()
            destination: Local path to save file

        Raises:
            TelegramError: If download fails
        """
        async with self._request_semaphore:
            try:
                # Construct download URL
                url = f"{self.config.api_url}/file/bot{self.config.bot_token}/{file_path}"

                # Use aiohttp to download
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as response:
                        response.raise_for_status()
                        with open(destination, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)

                logger.debug(f"Downloaded file to {destination}")
            except Exception as e:
                logger.error(f"Failed to download file {file_path}: {e}")
                raise

    async def close(self) -> None:
        """Close the bot connection."""
        await self.bot.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
