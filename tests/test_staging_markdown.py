"""Tests for staging markdown writer and reader."""

from datetime import datetime
from pathlib import Path

import pytest

from src.markdown.staging_writer import StagingWriter
from src.markdown.staging_reader import StagingReader
from src.telegram.fetcher import Message


@pytest.mark.asyncio
async def test_staging_writer_text_message(test_config, temp_dir, sample_message):
    """Test writing a text message to staging."""
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    writer = StagingWriter(test_config.markdown)

    # Write message
    filepath = await writer.append_entry(
        staging_dir=staging_dir,
        message=sample_message,
    )

    # Check file was created
    assert filepath.exists()
    assert filepath.name == "2026-01-05.md"

    # Check content
    content = filepath.read_text()
    assert "## 10:30" in content
    assert "This is a test message" in content
    assert "---" in content


@pytest.mark.asyncio
async def test_staging_writer_image_message(test_config, temp_dir, sample_image_message):
    """Test writing an image message to staging."""
    staging_dir = temp_dir / "staging" / "testuser"
    media_dir = temp_dir / "media" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    writer = StagingWriter(test_config.markdown)

    # Create actual media file
    media_file = media_dir / "sunset.jpg"
    media_file.write_text("fake image data")

    # Write message with media
    filepath = await writer.append_entry(
        staging_dir=staging_dir,
        message=sample_image_message,
        media_path=media_file,
    )

    # Check content
    content = filepath.read_text()
    assert "## 10:35 - [Image]" in content
    assert "sunset.jpg" in content
    assert "A beautiful sunset" in content


@pytest.mark.asyncio
async def test_staging_writer_multiple_messages(test_config, temp_dir, sample_message):
    """Test appending multiple messages to same file."""
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    writer = StagingWriter(test_config.markdown)

    # Write first message
    await writer.append_entry(staging_dir, sample_message)

    # Create second message
    message2 = Message(
        message_id=124,
        chat_id=456,
        user_id=789,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 11, 0, 0),
        message_type="text",
        text="Second message",
    )

    # Write second message
    filepath = await writer.append_entry(staging_dir, message2)

    # Check both messages are in file
    content = filepath.read_text()
    assert "## 10:30" in content
    assert "This is a test message" in content
    assert "## 11:00" in content
    assert "Second message" in content
    assert content.count("---") == 2  # Two separators


@pytest.mark.asyncio
async def test_staging_reader_text_message(test_config, temp_dir, sample_message):
    """Test reading a text message from staging."""
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Write message first
    writer = StagingWriter(test_config.markdown)
    filepath = await writer.append_entry(staging_dir, sample_message)

    # Read it back
    reader = StagingReader(test_config.markdown)
    messages = await reader.read_file(filepath, "testuser")

    # Should have one message
    assert len(messages) == 1

    # Check message content
    msg = messages[0]
    assert msg.message_type == "text"
    assert msg.text == "This is a test message"
    assert msg.timestamp.hour == 10
    assert msg.timestamp.minute == 30


@pytest.mark.asyncio
async def test_staging_reader_multiple_messages(test_config, temp_dir):
    """Test reading multiple messages from staging file."""
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    writer = StagingWriter(test_config.markdown)

    # Write multiple messages
    messages_to_write = [
        Message(
            message_id=i,
            chat_id=456,
            user_id=789,
            username="testuser",
            timestamp=datetime(2026, 1, 5, 10 + i, 0, 0),
            message_type="text",
            text=f"Message {i}",
        )
        for i in range(3)
    ]

    filepath = None
    for msg in messages_to_write:
        filepath = await writer.append_entry(staging_dir, msg)

    # Read them back
    reader = StagingReader(test_config.markdown)
    messages = await reader.read_file(filepath, "testuser")

    # Should have three messages
    assert len(messages) == 3

    # Check messages
    for i, msg in enumerate(messages):
        assert msg.text == f"Message {i}"


@pytest.mark.asyncio
async def test_staging_reader_image_message(test_config, temp_dir, sample_image_message):
    """Test reading an image message from staging."""
    staging_dir = temp_dir / "staging" / "testuser"
    media_dir = temp_dir / "media" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    # Create media file
    media_file = media_dir / "sunset.jpg"
    media_file.write_text("fake image")

    # Write image message
    writer = StagingWriter(test_config.markdown)
    filepath = await writer.append_entry(
        staging_dir,
        sample_image_message,
        media_path=media_file,
    )

    # Read it back
    reader = StagingReader(test_config.markdown)
    messages = await reader.read_file(filepath, "testuser")

    assert len(messages) == 1

    msg = messages[0]
    assert msg.message_type == "image"
    assert msg.caption == "A beautiful sunset"
    assert "sunset.jpg" in (msg.file_name or "")


@pytest.mark.asyncio
async def test_staging_roundtrip(test_config, temp_dir, sample_message):
    """Test write-read roundtrip preserves data."""
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)

    writer = StagingWriter(test_config.markdown)
    reader = StagingReader(test_config.markdown)

    # Write
    filepath = await writer.append_entry(staging_dir, sample_message)

    # Read
    messages = await reader.read_file(filepath, "testuser")

    # Compare
    assert len(messages) == 1
    msg = messages[0]

    assert msg.message_type == sample_message.message_type
    assert msg.text == sample_message.text
    assert msg.timestamp.date() == sample_message.timestamp.date()
    assert msg.timestamp.hour == sample_message.timestamp.hour
    assert msg.timestamp.minute == sample_message.timestamp.minute


@pytest.mark.asyncio
async def test_staging_reader_empty_file(test_config, temp_dir):
    """Test reading an empty staging file."""
    staging_file = temp_dir / "empty.md"
    staging_file.write_text("")

    reader = StagingReader(test_config.markdown)
    messages = await reader.read_file(staging_file, "testuser")

    assert len(messages) == 0


@pytest.mark.asyncio
async def test_staging_reader_malformed_file(test_config, temp_dir):
    """Test reading a malformed staging file."""
    staging_file = temp_dir / "malformed.md"
    staging_file.write_text("This is not valid staging markdown\nNo headers here!")

    reader = StagingReader(test_config.markdown)
    messages = await reader.read_file(staging_file, "testuser")

    # Should gracefully handle malformed content
    # Either return empty list or skip invalid entries
    assert isinstance(messages, list)
