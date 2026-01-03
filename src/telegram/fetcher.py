"""Message fetcher with incremental sync support."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional

from telegram import Update, Message as TGMessage

from src.core.config import UserConfig
from src.core.logger import get_logger
from src.core.state import StateManager, UserState
from src.telegram.client import TelegramClient
from src.utils.datetime_utils import parse_telegram_timestamp

logger = get_logger(__name__)


def generate_username_from_telegram(tg_user) -> str:
    """Generate a username from Telegram user info.

    Args:
        tg_user: Telegram User object

    Returns:
        Generated username
    """
    # Try to use Telegram username first
    if tg_user.username:
        return tg_user.username

    # Fall back to first_name + last_name
    parts = []
    if tg_user.first_name:
        parts.append(tg_user.first_name)
    if tg_user.last_name:
        parts.append(tg_user.last_name)

    if parts:
        username = "_".join(parts).lower().replace(" ", "_")
        # Remove special characters
        username = "".join(c for c in username if c.isalnum() or c == "_")
        return username

    # Last resort: use user ID
    return f"user_{tg_user.id}"


@dataclass
class Message:
    """Simplified message representation."""

    message_id: int
    chat_id: int
    user_id: int
    username: str
    timestamp: datetime
    message_type: Literal["text", "video", "audio", "voice", "image", "photo", "document", "link"]
    text: Optional[str] = None
    caption: Optional[str] = None
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    @classmethod
    def from_telegram_message(cls, tg_msg: TGMessage, username: str) -> "Message":
        """Create Message from Telegram Message object.

        Args:
            tg_msg: Telegram Message object
            username: Username for the chat

        Returns:
            Message instance
        """
        timestamp = parse_telegram_timestamp(tg_msg.date.timestamp())

        # Determine message type and extract file info
        message_type = "text"
        file_id = None
        file_name = None
        file_size = None
        mime_type = None
        text = tg_msg.text or tg_msg.caption
        caption = tg_msg.caption

        if tg_msg.video:
            message_type = "video"
            file_id = tg_msg.video.file_id
            file_name = tg_msg.video.file_name
            file_size = tg_msg.video.file_size
            mime_type = tg_msg.video.mime_type
        elif tg_msg.audio:
            message_type = "audio"
            file_id = tg_msg.audio.file_id
            file_name = tg_msg.audio.file_name
            file_size = tg_msg.audio.file_size
            mime_type = tg_msg.audio.mime_type
        elif tg_msg.voice:
            message_type = "voice"
            file_id = tg_msg.voice.file_id
            file_size = tg_msg.voice.file_size
            mime_type = tg_msg.voice.mime_type
        elif tg_msg.photo:
            message_type = "photo"
            # Get largest photo
            photo = max(tg_msg.photo, key=lambda p: p.file_size)
            file_id = photo.file_id
            file_size = photo.file_size
        elif tg_msg.document:
            message_type = "document"
            file_id = tg_msg.document.file_id
            file_name = tg_msg.document.file_name
            file_size = tg_msg.document.file_size
            mime_type = tg_msg.document.mime_type
        elif tg_msg.text and ("http://" in tg_msg.text or "https://" in tg_msg.text):
            message_type = "link"

        return cls(
            message_id=tg_msg.message_id,
            chat_id=tg_msg.chat_id,
            user_id=tg_msg.from_user.id if tg_msg.from_user else 0,
            username=username,
            timestamp=timestamp,
            message_type=message_type,
            text=text,
            caption=caption,
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
        )


class MessageFetcher:
    """Fetches messages from Telegram with incremental sync support."""

    def __init__(
        self,
        client: TelegramClient,
        state_manager: StateManager,
    ):
        """Initialize message fetcher.

        Args:
            client: Telegram client
            state_manager: State manager for tracking last message ID
        """
        self.client = client
        self.state_manager = state_manager

    async def fetch_new_messages(
        self,
        user: UserConfig,
        full_sync: bool = False,
    ) -> List[Message]:
        """Fetch new messages for a user.

        Args:
            user: User configuration
            full_sync: If True, fetch all messages (ignore last_message_id)

        Returns:
            List of new messages
        """
        user_state = self.state_manager.get_user_state(user.username)

        # Determine offset for fetching
        offset = None
        if not full_sync and user_state and user_state.last_message_id:
            # Fetch only messages after last processed ID
            # Note: Telegram's offset is update_id, not message_id
            # We'll filter by message_id after fetching
            pass

        logger.info(f"Fetching messages for user {user.username} (chat_id: {user.chat_id})")

        messages = []
        offset_update_id = None

        try:
            while True:
                # Fetch updates
                updates = await self.client.get_updates(
                    offset=offset_update_id,
                    limit=100,
                    timeout=0,
                )

                if not updates:
                    break

                # Process updates
                for update in updates:
                    # Update offset for next iteration
                    offset_update_id = update.update_id + 1

                    # Filter for messages from this user's chat
                    if update.message and update.message.chat_id == user.chat_id:
                        tg_msg = update.message

                        # Skip if message is from bot
                        if tg_msg.from_user and tg_msg.from_user.is_bot:
                            continue

                        # Filter by last_message_id if not full sync
                        if not full_sync and user_state and user_state.last_message_id:
                            if tg_msg.message_id <= user_state.last_message_id:
                                continue

                        # Convert to our Message format
                        msg = Message.from_telegram_message(tg_msg, user.username)
                        messages.append(msg)

                # If we got fewer updates than limit, we've reached the end
                if len(updates) < 100:
                    break

            logger.info(f"Fetched {len(messages)} new messages for {user.username}")
            return messages

        except Exception as e:
            logger.error(f"Error fetching messages for {user.username}: {e}")
            raise

    async def fetch_all_users(
        self,
        users: List[UserConfig],
        full_sync: bool = False,
    ) -> dict[str, List[Message]]:
        """Fetch messages for all users.

        Args:
            users: List of user configurations
            full_sync: If True, fetch all historical messages

        Returns:
            Dictionary mapping username to list of messages
        """
        results = {}

        for user in users:
            try:
                messages = await self.fetch_new_messages(user, full_sync=full_sync)
                results[user.username] = messages
            except Exception as e:
                logger.error(f"Failed to fetch messages for {user.username}: {e}")
                results[user.username] = []

        return results

    async def fetch_and_discover_users(
        self,
        full_sync: bool = False,
    ) -> Dict[str, tuple[UserConfig, List[Message]]]:
        """Fetch messages and auto-discover users who have messaged the bot.

        This method:
        1. Loads all previously discovered users from state.json
        2. Discovers any new users from current messages
        3. Returns all users (both existing and newly discovered)

        Args:
            full_sync: If True, fetch all historical messages

        Returns:
            Dictionary mapping username to (UserConfig, messages) tuple
        """
        logger.info("Fetching messages and discovering users...")

        # Load existing users from state
        state = self.state_manager.load()
        discovered_users: Dict[int, UserConfig] = {}  # chat_id -> UserConfig
        username_to_chatid: Dict[str, int] = {}  # username -> chat_id (for reverse lookup)

        for username, user_state in state.users.items():
            user_config = UserConfig(
                username=username,
                chat_id=user_state.chat_id,
                phone=user_state.phone,
            )
            discovered_users[user_state.chat_id] = user_config
            username_to_chatid[username] = user_state.chat_id
            logger.debug(f"Loaded existing user from state: {username} (chat_id: {user_state.chat_id})")

        user_messages: Dict[str, List[Message]] = {}  # username -> messages
        # Initialize message lists for all known users
        for username in state.users.keys():
            user_messages[username] = []

        offset_update_id = None
        newly_discovered_count = 0

        try:
            while True:
                # Fetch updates
                updates = await self.client.get_updates(
                    offset=offset_update_id,
                    limit=100,
                    timeout=0,
                )

                if not updates:
                    break

                # Process updates
                for update in updates:
                    # Update offset for next iteration
                    offset_update_id = update.update_id + 1

                    # Only process messages (not other update types)
                    if not update.message:
                        continue

                    tg_msg = update.message

                    # Skip if message is from bot
                    if tg_msg.from_user and tg_msg.from_user.is_bot:
                        continue

                    # Skip if no from_user (shouldn't happen but be safe)
                    if not tg_msg.from_user:
                        continue

                    chat_id = tg_msg.chat_id

                    # Discover user if not seen before
                    if chat_id not in discovered_users:
                        username = generate_username_from_telegram(tg_msg.from_user)

                        # Check if username already exists (from different chat_id)
                        existing_usernames = list(username_to_chatid.keys())
                        original_username = username
                        counter = 1
                        while username in existing_usernames:
                            username = f"{original_username}_{counter}"
                            counter += 1

                        user_config = UserConfig(
                            username=username,
                            chat_id=chat_id,
                            phone=None,  # Not available from bot API
                        )
                        discovered_users[chat_id] = user_config
                        username_to_chatid[username] = chat_id
                        user_messages[username] = []
                        newly_discovered_count += 1
                        logger.info(f"Discovered new user: {username} (chat_id: {chat_id})")

                    # Get user config
                    user_config = discovered_users[chat_id]
                    username = user_config.username

                    # Check if we should process this message
                    user_state = self.state_manager.get_user_state(username)
                    if not full_sync and user_state and user_state.last_message_id:
                        if tg_msg.message_id <= user_state.last_message_id:
                            continue

                    # Convert to our Message format
                    msg = Message.from_telegram_message(tg_msg, username)
                    user_messages[username].append(msg)

                # If we got fewer updates than limit, we've reached the end
                if len(updates) < 100:
                    break

            # Build result dictionary - include ALL discovered users (even those with no new messages)
            results = {}
            for chat_id, user_config in discovered_users.items():
                username = user_config.username
                messages = user_messages.get(username, [])
                results[username] = (user_config, messages)

            total_users = len(discovered_users)
            total_messages = sum(len(m) for m in user_messages.values())

            if newly_discovered_count > 0:
                logger.info(f"Discovered {newly_discovered_count} new users")
            logger.info(f"Total users: {total_users}, New messages: {total_messages}")

            return results

        except Exception as e:
            logger.error(f"Error during user discovery: {e}")
            raise
