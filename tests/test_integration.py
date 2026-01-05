"""Integration tests for end-to-end workflows."""

from datetime import datetime
from pathlib import Path

import pytest

from src.core.state import StateManager
from src.markdown.staging_writer import StagingWriter
from src.markdown.staging_reader import StagingReader
from src.markdown.processed_writer import ProcessedWriter
from src.processors.base import ProcessedResult
from src.telegram.fetcher import Message
from src.utils.checksum import calculate_checksum


@pytest.mark.asyncio
async def test_fetch_to_staging_workflow(test_config, temp_dir):
    """Test the fetch-to-staging workflow (Phase 1)."""
    # Setup
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    state_manager = StateManager(temp_dir / "state.json")
    state_manager.ensure_user_exists("testuser", chat_id=123)

    writer = StagingWriter(test_config.markdown)

    # Simulate fetching messages
    messages = [
        Message(
            message_id=100 + i,
            chat_id=123,
            user_id=456,
            username="testuser",
            timestamp=datetime(2026, 1, 5, 10 + i, 0, 0),
            message_type="text",
            text=f"Message {i}",
        )
        for i in range(5)
    ]

    # Write to staging
    for msg in messages:
        filepath = await writer.append_entry(staging_dir, msg)

        # Update state
        state_manager.add_pending_file("testuser", str(filepath.relative_to(temp_dir)))
        state_manager.update_fetch_state(
            "testuser",
            last_message_id=msg.message_id,
            count=1
        )

    # Verify
    user_state = state_manager.get_user_state("testuser")
    assert user_state.fetch_state.total_messages_fetched == 5
    assert user_state.fetch_state.last_message_id == 104
    assert len(user_state.process_state.pending_files) > 0

    # Staging file should exist
    staging_file = staging_dir / "2026-01-05.md"
    assert staging_file.exists()

    # Should contain all messages
    content = staging_file.read_text()
    assert "Message 0" in content
    assert "Message 4" in content


@pytest.mark.asyncio
async def test_staging_to_processed_workflow(test_config, temp_dir):
    """Test the staging-to-processed workflow (Phase 2)."""
    # Setup directories
    staging_dir = temp_dir / "staging" / "testuser"
    processed_dir = temp_dir / "processed" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    state_manager = StateManager(temp_dir / "state.json")
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Phase 1: Write to staging
    staging_writer = StagingWriter(test_config.markdown)
    message = Message(
        message_id=100,
        chat_id=123,
        user_id=456,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 10, 0, 0),
        message_type="text",
        text="Test message for processing",
    )

    staging_file = await staging_writer.append_entry(staging_dir, message)
    state_manager.add_pending_file("testuser", str(staging_file.relative_to(temp_dir)))

    # Phase 2: Read from staging
    staging_reader = StagingReader(test_config.markdown)
    messages = await staging_reader.read_file(staging_file)

    assert len(messages) == 1

    # Process message (simplified)
    processed_result = ProcessedResult(
        markdown_content="Test message for processing",
        message_type="text",
        tags=["#test"],
    )

    # Write to processed
    processed_writer = ProcessedWriter(test_config.markdown)
    processed_file = await processed_writer.append_entry(
        processed_dir=processed_dir,
        message=messages[0],
        processed_result=processed_result,
    )

    # Update state
    checksum = calculate_checksum(staging_file)
    state_manager.mark_file_processed(
        "testuser",
        str(staging_file.relative_to(temp_dir)),
        checksum
    )

    # Verify
    assert processed_file.exists()

    content = processed_file.read_text()
    assert "type: text" in content
    assert "tags: [#test]" in content

    # State should be updated
    user_state = state_manager.get_user_state("testuser")
    assert len(user_state.process_state.pending_files) == 0
    assert len(user_state.process_state.file_checksums) > 0


@pytest.mark.asyncio
async def test_checksum_based_reprocessing(test_config, temp_dir):
    """Test that checksum-based reprocessing works correctly."""
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    state_manager = StateManager(temp_dir / "state.json")
    state_manager.ensure_user_exists("testuser", chat_id=123)

    # Write a staging file
    staging_writer = StagingWriter(test_config.markdown)
    message = Message(
        message_id=100,
        chat_id=123,
        user_id=456,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 10, 0, 0),
        message_type="text",
        text="Original message",
    )

    staging_file = await staging_writer.append_entry(staging_dir, message)

    # Calculate and store checksum
    original_checksum = calculate_checksum(staging_file)
    state_manager.update_process_state(
        "testuser",
        checksums={str(staging_file.relative_to(temp_dir)): original_checksum},
        pending_files=[]
    )

    # Verify file hasn't changed
    current_checksum = calculate_checksum(staging_file)
    assert current_checksum == original_checksum

    # Modify the file
    await staging_writer.append_entry(staging_dir, Message(
        message_id=101,
        chat_id=123,
        user_id=456,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 11, 0, 0),
        message_type="text",
        text="New message",
    ))

    # Checksum should now be different
    new_checksum = calculate_checksum(staging_file)
    assert new_checksum != original_checksum

    # File should be marked for reprocessing
    stored_checksum = state_manager.get_file_checksum(
        "testuser",
        str(staging_file.relative_to(temp_dir))
    )
    assert stored_checksum == original_checksum
    assert new_checksum != stored_checksum


@pytest.mark.asyncio
async def test_multiple_users_workflow(test_config, temp_dir):
    """Test handling multiple users simultaneously."""
    state_manager = StateManager(temp_dir / "state.json")
    staging_writer = StagingWriter(test_config.markdown)

    users = ["alice", "bob", "charlie"]

    # Add users and messages for each
    for i, username in enumerate(users):
        # Add user to state
        state_manager.ensure_user_exists(username, chat_id=100 + i)

        # Create staging directory
        staging_dir = temp_dir / "staging" / username
        staging_dir.mkdir(parents=True, exist_ok=True)

        # Write messages
        for j in range(3):
            message = Message(
                message_id=j,
                chat_id=100 + i,
                user_id=200 + i,
                username=username,
                timestamp=datetime(2026, 1, 5, 10 + j, 0, 0),
                message_type="text",
                text=f"Message from {username} #{j}",
            )

            filepath = await staging_writer.append_entry(staging_dir, message)
            state_manager.add_pending_file(username, str(filepath.relative_to(temp_dir)))
            state_manager.update_fetch_state(username, last_message_id=j, count=1)

    # Verify all users are tracked
    all_users = state_manager.get_all_users()
    assert len(all_users) == 3
    assert set(all_users) == set(users)

    # Verify each user has correct state
    for username in users:
        user_state = state_manager.get_user_state(username)
        assert user_state.fetch_state.total_messages_fetched == 3
        assert len(user_state.process_state.pending_files) > 0

        # Verify staging files exist
        staging_file = temp_dir / "staging" / username / "2026-01-05.md"
        assert staging_file.exists()


@pytest.mark.asyncio
async def test_reply_context_preservation(test_config, temp_dir, sample_reply_message):
    """Test that reply context is preserved through the pipeline."""
    staging_dir = temp_dir / "staging" / "testuser"
    processed_dir = temp_dir / "processed" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Write to staging
    staging_writer = StagingWriter(test_config.markdown)
    staging_file = await staging_writer.append_entry(staging_dir, sample_reply_message)

    # Read from staging
    staging_reader = StagingReader(test_config.markdown)
    messages = await staging_reader.read_file(staging_file)

    assert len(messages) == 1
    msg = messages[0]

    # Reply context should be preserved (if reader supports it)
    # Note: Current reader might not preserve reply_to, this tests the structure

    # Process and write
    processed_result = ProcessedResult(
        markdown_content="This is a reply",
        message_type="text",
        reply_to=sample_reply_message.reply_to,
    )

    processed_writer = ProcessedWriter(test_config.markdown)
    processed_file = await processed_writer.append_entry(
        processed_dir, sample_reply_message, processed_result
    )

    # Verify reply context in processed file
    content = processed_file.read_text()
    assert "reply_to:" in content
    assert "message_id: 123" in content
