"""Pytest configuration and shared fixtures."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict

import pytest

from src.core.config import Config, load_config
from src.core.state import StateManager
from src.telegram.fetcher import Message


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config_dict = {
        "telegram": {
            "bot_token": "test_token",
            "api_url": "https://api.telegram.org",
            "timeout": 30,
            "retry_attempts": 3,
        },
        "users": [],
        "storage": {
            "base_dir": str(temp_dir),
            "staging_dir": "staging",
            "processed_dir": "processed",
            "media_dir": "media",
            "staging_retention": {
                "policy": "keep_days",
                "days": 7,
            },
        },
        "transcription": {
            "enabled": True,
            "provider": "ollama",
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "whisper",
                "timeout": 300,
            },
            "youtube_prefer_transcript": True,
        },
        "summarization": {
            "enabled": True,
            "provider": "ollama",
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama2",
                "temperature": 0.7,
                "max_tokens": 500,
            },
            "prompts": {
                "video_summary": "Summarize the video.",
                "audio_summary": "Summarize the audio.",
                "article_summary": "Summarize the article.",
                "youtube_summary": "Summarize the YouTube video.",
            },
        },
        "ocr": {
            "enabled": True,
            "provider": "tesseract",
            "tesseract": {
                "languages": ["eng"],
                "config": "--psm 3",
            },
        },
        "links": {
            "enabled": True,
            "timeout": 10,
            "user_agent": "Trudy/2.0",
            "extract": {
                "title": True,
                "description": True,
                "opengraph": False,
                "favicon": False,
            },
        },
        "tagging": {
            "enabled": True,
            "rules": [
                {"pattern": "test", "tag": "#test"},
            ],
            "ai_tagging": {
                "enabled": False,
            },
        },
        "processing": {
            "max_workers": 3,
            "skip_errors": True,
            "retry_failed": True,
            "max_retries": 3,
            "show_progress": True,
            "report_interval": 10,
        },
        "logging": {
            "level": "ERROR",  # Suppress logs during tests
            "file": str(temp_dir / "trudy.log"),
            "error_file": str(temp_dir / "errors.log"),
            "max_bytes": 10485760,
            "backup_count": 5,
        },
        "markdown": {
            "timezone": "UTC",
            "timestamp_format": "HH:mm",
            "date_format": "YYYY-MM-DD",
            "wikilink_style": "obsidian",
            "include_message_id": False,
            "include_edit_history": True,
        },
    }

    # Create a Config object from dict
    return Config(**config_dict)


@pytest.fixture
def state_manager(temp_dir):
    """Create a test state manager."""
    state_file = temp_dir / "state.json"
    return StateManager(state_file)


@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    return Message(
        message_id=123,
        chat_id=456,
        user_id=789,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 10, 30, 0),
        message_type="text",
        text="This is a test message",
        caption=None,
        file_id=None,
        file_name=None,
        file_size=None,
        mime_type=None,
        reply_to=None,
        forwarded_from=None,
        edited_at=None,
    )


@pytest.fixture
def sample_image_message():
    """Create a sample image message for testing."""
    return Message(
        message_id=124,
        chat_id=456,
        user_id=789,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 10, 35, 0),
        message_type="image",
        text=None,
        caption="A beautiful sunset",
        file_id="file_123",
        file_name="sunset.jpg",
        file_size=1024000,
        mime_type="image/jpeg",
        reply_to=None,
        forwarded_from=None,
        edited_at=None,
    )


@pytest.fixture
def sample_reply_message():
    """Create a sample message with reply context."""
    return Message(
        message_id=125,
        chat_id=456,
        user_id=789,
        username="testuser",
        timestamp=datetime(2026, 1, 5, 10, 40, 0),
        message_type="text",
        text="This is a reply",
        caption=None,
        file_id=None,
        file_name=None,
        file_size=None,
        mime_type=None,
        reply_to={
            "message_id": 123,
            "timestamp": "2026-01-05T10:30:00",
            "preview": "This is a test message",
        },
        forwarded_from=None,
        edited_at=None,
    )


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
