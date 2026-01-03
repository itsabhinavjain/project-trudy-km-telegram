"""State management for tracking message processing across users."""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field


class UserState(BaseModel):
    """State information for a single user."""

    chat_id: int = Field(..., description="Telegram chat ID")
    phone: Optional[str] = Field(None, description="User's phone number")
    first_message_time: Optional[datetime] = Field(
        None, description="Timestamp of first message ever received"
    )
    last_fetch_time: Optional[datetime] = Field(
        None, description="Timestamp of last fetch operation"
    )
    last_message_id: Optional[int] = Field(None, description="Last processed message ID")
    total_messages: int = Field(default=0, description="Total messages processed")
    last_fetch_count: int = Field(default=0, description="Messages fetched in last run")


class Statistics(BaseModel):
    """Global statistics across all users."""

    total_messages_processed: int = Field(default=0, description="Total messages processed")
    total_media_downloaded: int = Field(default=0, description="Total media files downloaded")
    total_transcriptions: int = Field(default=0, description="Total transcriptions completed")
    total_summaries: int = Field(default=0, description="Total summaries generated")


class State(BaseModel):
    """Application state."""

    version: str = Field(default="1.0", description="State schema version")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last state update time"
    )
    users: Dict[str, UserState] = Field(default_factory=dict, description="User states")
    statistics: Statistics = Field(default_factory=Statistics, description="Global statistics")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class StateManager:
    """Thread-safe state manager for reading and writing state file."""

    def __init__(self, state_file: Path = Path("data/state.json")):
        """Initialize state manager.

        Args:
            state_file: Path to state JSON file
        """
        self.state_file = state_file
        self._lock = threading.Lock()
        self._state: Optional[State] = None

    def load(self) -> State:
        """Load state from file or create new state if file doesn't exist.

        Returns:
            Loaded or new state object
        """
        with self._lock:
            if not self.state_file.exists():
                self._state = State()
                self._ensure_directory()
                self._write_state()
                return self._state

            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = State(**data)
            except (json.JSONDecodeError, ValueError) as e:
                # If state file is corrupted, create backup and start fresh
                backup_file = self.state_file.with_suffix(".json.backup")
                if self.state_file.exists():
                    self.state_file.rename(backup_file)
                self._state = State()
                self._write_state()

            return self._state

    def save(self, state: State) -> None:
        """Save state to file atomically.

        Args:
            state: State object to save
        """
        with self._lock:
            state.last_updated = datetime.utcnow()
            self._state = state
            self._write_state()

    def _write_state(self) -> None:
        """Write state to file atomically using temporary file."""
        self._ensure_directory()

        # Write to temporary file first
        temp_file = self.state_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                self._state.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Atomic rename
        temp_file.replace(self.state_file)

    def _ensure_directory(self) -> None:
        """Ensure state file directory exists."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def get_user_state(self, username: str) -> Optional[UserState]:
        """Get state for a specific user.

        Args:
            username: Username to lookup

        Returns:
            User state or None if user doesn't exist
        """
        if self._state is None:
            self.load()
        return self._state.users.get(username)

    def update_user_state(
        self,
        username: str,
        chat_id: int,
        phone: Optional[str] = None,
        message_id: Optional[int] = None,
        message_count: int = 0,
        first_message_time: Optional[datetime] = None,
    ) -> None:
        """Update state for a specific user.

        Args:
            username: Username to update
            chat_id: Telegram chat ID
            phone: Phone number (optional)
            message_id: Latest message ID processed
            message_count: Number of messages processed in this batch
            first_message_time: Timestamp of first message (for new users)
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            # Create new user state
            user_state = UserState(
                chat_id=chat_id,
                phone=phone,
                first_message_time=first_message_time or datetime.utcnow(),
            )
            self._state.users[username] = user_state

        # Update fields
        if message_id is not None:
            user_state.last_message_id = message_id
        user_state.last_fetch_time = datetime.utcnow()
        user_state.total_messages += message_count
        user_state.last_fetch_count = message_count

        # Save updated state
        self.save(self._state)

    def increment_statistics(
        self,
        messages: int = 0,
        media: int = 0,
        transcriptions: int = 0,
        summaries: int = 0,
    ) -> None:
        """Increment global statistics.

        Args:
            messages: Number of messages to add
            media: Number of media files to add
            transcriptions: Number of transcriptions to add
            summaries: Number of summaries to add
        """
        if self._state is None:
            self.load()

        self._state.statistics.total_messages_processed += messages
        self._state.statistics.total_media_downloaded += media
        self._state.statistics.total_transcriptions += transcriptions
        self._state.statistics.total_summaries += summaries

        self.save(self._state)

    def get_statistics(self) -> Statistics:
        """Get global statistics.

        Returns:
            Global statistics object
        """
        if self._state is None:
            self.load()
        return self._state.statistics
