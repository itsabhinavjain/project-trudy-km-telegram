"""State management for tracking message processing across users."""

import json
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FetchState(BaseModel):
    """State tracking for message fetching (Phase 1)."""

    last_message_id: Optional[int] = Field(None, description="Last fetched Telegram message ID")
    last_fetch_time: Optional[datetime] = Field(None, description="Timestamp of last fetch operation")
    total_messages_fetched: int = Field(default=0, description="Cumulative messages fetched")


class ProcessState(BaseModel):
    """State tracking for message processing (Phase 2)."""

    last_processed_date: Optional[str] = Field(None, description="Last date fully processed (YYYY-MM-DD)")
    last_process_time: Optional[datetime] = Field(None, description="Timestamp of last process operation")
    total_messages_processed: int = Field(default=0, description="Cumulative messages processed")
    file_checksums: Dict[str, str] = Field(
        default_factory=dict, description="SHA-256 checksums of staging files (path -> checksum)"
    )
    pending_files: List[str] = Field(
        default_factory=list, description="Staging files pending processing"
    )


class UserState(BaseModel):
    """State information for a single user."""

    chat_id: int = Field(..., description="Telegram chat ID")
    phone: Optional[str] = Field(None, description="User's phone number")
    first_seen: Optional[datetime] = Field(
        None, description="Timestamp of first message ever received"
    )
    last_seen: Optional[datetime] = Field(
        None, description="Timestamp of most recent message"
    )
    fetch_state: FetchState = Field(default_factory=FetchState, description="Fetching state")
    process_state: ProcessState = Field(default_factory=ProcessState, description="Processing state")


class Statistics(BaseModel):
    """Global statistics across all users."""

    total_users: int = Field(default=0, description="Total users discovered")
    total_messages_fetched: int = Field(default=0, description="Total messages fetched")
    total_messages_processed: int = Field(default=0, description="Total messages processed")
    total_media: int = Field(default=0, description="Total media files downloaded")
    total_transcriptions: int = Field(default=0, description="Total transcriptions completed")
    total_summaries: int = Field(default=0, description="Total summaries generated")
    total_ocr: int = Field(default=0, description="Total OCR operations performed")
    total_tags: int = Field(default=0, description="Total tags generated")
    total_links_extracted: int = Field(default=0, description="Total link metadata extracted")


class State(BaseModel):
    """Application state."""

    version: str = Field(default="2.0", description="State schema version")
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

        # Create backup before writing
        if self.state_file.exists():
            backup_file = self.state_file.with_suffix(".json.bak")
            shutil.copy2(self.state_file, backup_file)

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

    @property
    def state(self) -> State:
        """Get current state, loading if necessary.

        Returns:
            Current state object
        """
        if self._state is None:
            self.load()
        return self._state

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

    def ensure_user_exists(
        self,
        username: str,
        chat_id: int,
        phone: Optional[str] = None,
        first_seen: Optional[datetime] = None,
    ) -> UserState:
        """Ensure user exists in state, create if not.

        Args:
            username: Username
            chat_id: Telegram chat ID
            phone: Phone number (optional)
            first_seen: First seen timestamp (optional)

        Returns:
            User state object
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            # Create new user state
            user_state = UserState(
                chat_id=chat_id,
                phone=phone,
                first_seen=first_seen or datetime.utcnow(),
            )
            self._state.users[username] = user_state
            self._state.statistics.total_users = len(self._state.users)
            self.save(self._state)

        return user_state

    def update_fetch_state(
        self,
        username: str,
        last_message_id: Optional[int] = None,
        message_count: int = 0,
    ) -> None:
        """Update fetch state for a user.

        Args:
            username: Username to update
            last_message_id: Latest message ID fetched
            message_count: Number of messages fetched in this batch
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            raise ValueError(f"User {username} not found in state. Call ensure_user_exists first.")

        # Update fetch state
        if last_message_id is not None:
            user_state.fetch_state.last_message_id = last_message_id
        user_state.fetch_state.last_fetch_time = datetime.utcnow()
        user_state.fetch_state.total_messages_fetched += message_count
        user_state.last_seen = datetime.utcnow()

        # Update global statistics
        self._state.statistics.total_messages_fetched += message_count

        # Save updated state
        self.save(self._state)

    def add_pending_file(self, username: str, filepath: str) -> None:
        """Add a staging file to pending processing list.

        Args:
            username: Username
            filepath: Path to staging file (relative or absolute)
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            raise ValueError(f"User {username} not found in state.")

        # Convert to string and add if not already present
        filepath_str = str(filepath)
        if filepath_str not in user_state.process_state.pending_files:
            user_state.process_state.pending_files.append(filepath_str)
            self.save(self._state)

    def get_pending_files(self, username: str) -> List[str]:
        """Get list of pending staging files for a user.

        Args:
            username: Username

        Returns:
            List of pending file paths
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            return []

        return user_state.process_state.pending_files.copy()

    def mark_file_processed(
        self,
        username: str,
        filepath: str,
        checksum: str,
        message_count: int = 0,
    ) -> None:
        """Mark a staging file as processed.

        Args:
            username: Username
            filepath: Path to staging file
            checksum: SHA-256 checksum of the file
            message_count: Number of messages processed from this file
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            raise ValueError(f"User {username} not found in state.")

        # Update checksum
        filepath_str = str(filepath)
        user_state.process_state.file_checksums[filepath_str] = checksum

        # Remove from pending
        if filepath_str in user_state.process_state.pending_files:
            user_state.process_state.pending_files.remove(filepath_str)

        # Update process state
        user_state.process_state.last_process_time = datetime.utcnow()
        user_state.process_state.total_messages_processed += message_count

        # Update global statistics
        self._state.statistics.total_messages_processed += message_count

        # Save updated state
        self.save(self._state)

    def get_file_checksum(self, username: str, filepath: str) -> Optional[str]:
        """Get stored checksum for a file.

        Args:
            username: Username
            filepath: Path to staging file

        Returns:
            Stored checksum or None if not found
        """
        if self._state is None:
            self.load()

        user_state = self._state.users.get(username)
        if user_state is None:
            return None

        return user_state.process_state.file_checksums.get(str(filepath))

    def increment_statistics(
        self,
        media: int = 0,
        transcriptions: int = 0,
        summaries: int = 0,
        ocr: int = 0,
        tags: int = 0,
        links: int = 0,
    ) -> None:
        """Increment global statistics.

        Args:
            media: Number of media files to add
            transcriptions: Number of transcriptions to add
            summaries: Number of summaries to add
            ocr: Number of OCR operations to add
            tags: Number of tags to add
            links: Number of link extractions to add
        """
        if self._state is None:
            self.load()

        self._state.statistics.total_media += media
        self._state.statistics.total_transcriptions += transcriptions
        self._state.statistics.total_summaries += summaries
        self._state.statistics.total_ocr += ocr
        self._state.statistics.total_tags += tags
        self._state.statistics.total_links_extracted += links

        self.save(self._state)

    def get_statistics(self) -> Statistics:
        """Get global statistics.

        Returns:
            Global statistics object
        """
        if self._state is None:
            self.load()
        return self._state.statistics
