"""Tests for state management."""

from datetime import datetime
from pathlib import Path

import pytest

from src.core.state import StateManager, UserState, FetchState, ProcessState


def test_state_manager_initialization(temp_dir):
    """Test state manager initialization."""
    state_file = temp_dir / "state.json"
    manager = StateManager(state_file)

    assert manager.state_file == state_file
    assert manager.state is not None
    assert len(manager.state.users) == 0


def test_add_user(state_manager):
    """Test adding a new user."""
    state_manager.ensure_user_exists("testuser", chat_id=123, phone="+1234567890")

    user_state = state_manager.get_user_state("testuser")

    assert user_state is not None
    assert user_state.chat_id == 123
    assert user_state.phone == "+1234567890"
    assert user_state.fetch_state is not None
    assert user_state.process_state is not None


def test_get_all_users(state_manager):
    """Test getting all users."""
    # Add multiple users
    state_manager.ensure_user_exists("user1", chat_id=111)
    state_manager.ensure_user_exists("user2", chat_id=222)
    state_manager.ensure_user_exists("user3", chat_id=333)

    users = list(state_manager.state.users.keys())

    assert len(users) == 3
    assert "user1" in users
    assert "user2" in users
    assert "user3" in users


def test_update_fetch_state(state_manager):
    """Test updating fetch state."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Update fetch state
    state_manager.update_fetch_state(
        username="testuser",
        last_message_id=456,
        message_count=10
    )

    user_state = state_manager.get_user_state("testuser")

    assert user_state.fetch_state.last_message_id == 456
    assert user_state.fetch_state.total_messages_fetched == 10
    assert user_state.fetch_state.last_fetch_time is not None


def test_update_fetch_state_incremental(state_manager):
    """Test incremental fetch state updates."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # First update
    state_manager.update_fetch_state("testuser", last_message_id=100, message_count=5)

    # Second update
    state_manager.update_fetch_state("testuser", last_message_id=110, message_count=3)

    user_state = state_manager.get_user_state("testuser")

    assert user_state.fetch_state.last_message_id == 110
    assert user_state.fetch_state.total_messages_fetched == 8  # 5 + 3


def test_update_process_state(state_manager):
    """Test updating process state."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Mark files as processed with checksums
    state_manager.mark_file_processed("testuser", "2026-01-05.md", "abc123")
    state_manager.mark_file_processed("testuser", "2026-01-06.md", "def456")

    user_state = state_manager.get_user_state("testuser")

    assert user_state.process_state.file_checksums["2026-01-05.md"] == "abc123"
    assert user_state.process_state.file_checksums["2026-01-06.md"] == "def456"
    assert user_state.process_state.last_process_time is not None


def test_get_pending_files(state_manager):
    """Test getting pending files."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Add pending files
    state_manager.add_pending_file("testuser", "staging/testuser/2026-01-05.md")
    state_manager.add_pending_file("testuser", "staging/testuser/2026-01-06.md")

    result = state_manager.get_pending_files("testuser")

    assert "staging/testuser/2026-01-05.md" in result
    assert "staging/testuser/2026-01-06.md" in result
    assert len(result) == 2


def test_mark_file_processed(state_manager):
    """Test marking a file as processed."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Add pending files
    state_manager.add_pending_file("testuser", "file1.md")
    state_manager.add_pending_file("testuser", "file2.md")
    state_manager.add_pending_file("testuser", "file3.md")

    # Mark one as processed
    state_manager.mark_file_processed("testuser", "file1.md", "checksum123")

    user_state = state_manager.get_user_state("testuser")

    # File should be removed from pending
    assert "file1.md" not in user_state.process_state.pending_files
    assert "file2.md" in user_state.process_state.pending_files
    assert "file3.md" in user_state.process_state.pending_files

    # Checksum should be stored
    assert user_state.process_state.file_checksums["file1.md"] == "checksum123"


def test_add_pending_file(state_manager):
    """Test adding a pending file."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    state_manager.add_pending_file("testuser", "new_file.md")

    pending = state_manager.get_pending_files("testuser")

    assert "new_file.md" in pending


def test_add_pending_file_no_duplicates(state_manager):
    """Test that adding same file twice doesn't create duplicates."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    state_manager.add_pending_file("testuser", "file.md")
    state_manager.add_pending_file("testuser", "file.md")

    pending = state_manager.get_pending_files("testuser")

    assert pending.count("file.md") == 1


def test_state_persistence(temp_dir):
    """Test that state persists to disk and can be reloaded."""
    state_file = temp_dir / "state.json"

    # Create state and add data
    manager1 = StateManager(state_file)
    manager1.ensure_user_exists("testuser", chat_id=123, phone="+1234567890")
    manager1.update_fetch_state("testuser", last_message_id=456, message_count=10)
    # State is automatically saved by update methods

    # Load state in new manager
    manager2 = StateManager(state_file)

    user_state = manager2.get_user_state("testuser")

    assert user_state is not None
    assert user_state.chat_id == 123
    assert user_state.phone == "+1234567890"
    assert user_state.fetch_state.last_message_id == 456
    assert user_state.fetch_state.total_messages_fetched == 10


def test_get_checksum(state_manager):
    """Test getting checksum for a file."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Mark file as processed with checksum
    state_manager.mark_file_processed("testuser", "file1.md", "abc123")

    checksum = state_manager.get_file_checksum("testuser", "file1.md")

    assert checksum == "abc123"


def test_get_checksum_missing_file(state_manager):
    """Test getting checksum for non-existent file."""
    state_manager.ensure_user_exists("testuser", chat_id=123)

    checksum = state_manager.get_file_checksum("testuser", "nonexistent.md")

    assert checksum is None


def test_state_backup_on_update(temp_dir):
    """Test that state backup is created on updates."""
    state_file = temp_dir / "state.json"
    backup_file = temp_dir / "state.json.bak"  # Actual backup extension used

    manager = StateManager(state_file)
    manager.ensure_user_exists("testuser", chat_id=123)
    # State is automatically saved

    # Make another change to trigger backup
    manager.update_fetch_state("testuser", last_message_id=456, message_count=10)
    # State is automatically saved with backup

    # Backup should exist
    assert backup_file.exists()
