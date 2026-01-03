"""Configuration management for Trudy Telegram system."""

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class TelegramConfig(BaseModel):
    """Telegram Bot API configuration."""

    bot_token: str = Field(..., description="Telegram bot token from @BotFather")
    api_url: str = Field(
        default="https://api.telegram.org", description="Telegram API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")


class UserConfig(BaseModel):
    """User configuration."""

    username: str = Field(..., description="Username for folder organization")
    phone: Optional[str] = Field(None, description="User's phone number")
    chat_id: int = Field(..., description="Telegram chat ID for this user")


class OllamaConfig(BaseModel):
    """Ollama API configuration."""

    base_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    model: str = Field(default="whisper", description="Model name")
    timeout: int = Field(default=300, description="Request timeout in seconds")


class TranscriptionConfig(BaseModel):
    """Transcription configuration."""

    enabled: bool = Field(default=True, description="Enable transcription")
    provider: Literal["ollama", "remote"] = Field(
        default="ollama", description="Transcription provider"
    )
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    youtube_prefer_transcript: bool = Field(
        default=True, description="Prefer YouTube transcript API over downloading"
    )


class OllamaSummarizerConfig(BaseModel):
    """Ollama summarization configuration."""

    base_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    model: str = Field(default="llama2", description="Model name for summarization")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: int = Field(default=500, description="Maximum tokens to generate")


class ClaudeSummarizerConfig(BaseModel):
    """Claude Code CLI summarization configuration."""

    cli_path: str = Field(default="claude", description="Path to Claude Code CLI")
    model: str = Field(default="claude-sonnet-4-5", description="Claude model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")


class SummarizationPromptsConfig(BaseModel):
    """Summarization prompts for different content types."""

    video_summary: str = Field(
        default="Summarize the key points from this video transcript in 3-5 bullet points.",
        description="Prompt for video summarization",
    )
    audio_summary: str = Field(
        default="Summarize the main topics discussed in this audio recording.",
        description="Prompt for audio summarization",
    )
    article_summary: str = Field(
        default="Provide a concise summary of this article in 2-3 paragraphs.",
        description="Prompt for article summarization",
    )
    youtube_summary: str = Field(
        default="Summarize this YouTube video, highlighting key takeaways.",
        description="Prompt for YouTube video summarization",
    )


class SummarizationConfig(BaseModel):
    """Summarization configuration."""

    enabled: bool = Field(default=True, description="Enable summarization")
    provider: Literal["ollama", "claude"] = Field(
        default="ollama", description="Summarization provider"
    )
    ollama: OllamaSummarizerConfig = Field(default_factory=OllamaSummarizerConfig)
    claude: ClaudeSummarizerConfig = Field(default_factory=ClaudeSummarizerConfig)
    prompts: SummarizationPromptsConfig = Field(default_factory=SummarizationPromptsConfig)


class StorageConfig(BaseModel):
    """Storage paths configuration."""

    base_dir: str = Field(default="./data", description="Base data directory")
    notes_subdir: str = Field(default="notes", description="Notes subdirectory name")
    media_subdir: str = Field(default="media", description="Media subdirectory name")

    @property
    def base_path(self) -> Path:
        """Get base directory as Path object."""
        return Path(self.base_dir).resolve()

    def get_user_notes_dir(self, username: str) -> Path:
        """Get notes directory for a specific user."""
        return self.base_path / "users" / username / self.notes_subdir

    def get_user_media_dir(self, username: str) -> Path:
        """Get media directory for a specific user."""
        return self.base_path / "users" / username / self.media_subdir


class ProcessingConfig(BaseModel):
    """Processing configuration."""

    max_concurrent: int = Field(default=3, description="Max concurrent processing tasks")
    skip_errors: bool = Field(
        default=True, description="Continue processing on individual errors"
    )
    retry_failed: bool = Field(default=True, description="Retry failed processing")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    file: str = Field(default="./logs/trudy.log", description="Log file path")
    error_file: str = Field(default="./logs/errors.log", description="Error log file path")
    max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")


class MarkdownConfig(BaseModel):
    """Markdown formatting configuration."""

    timezone: str = Field(default="UTC", description="Timezone for timestamps")
    timestamp_format: str = Field(default="HH:MM", description="Time format for headers")
    include_message_id: bool = Field(
        default=False, description="Include Telegram message ID in comments"
    )
    wikilink_style: Literal["obsidian", "standard"] = Field(
        default="obsidian", description="Wikilink style"
    )


class Config(BaseModel):
    """Main configuration."""

    telegram: TelegramConfig
    users: list[UserConfig] = Field(
        default_factory=list,
        description="Optional: Pre-configured users. If empty, users are auto-discovered.",
    )
    storage: StorageConfig = Field(default_factory=StorageConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    summarization: SummarizationConfig = Field(default_factory=SummarizationConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)

    @field_validator("users")
    @classmethod
    def validate_users(cls, users: list[UserConfig]) -> list[UserConfig]:
        """Validate that usernames are unique."""
        if not users:
            return users
        usernames = [user.username for user in users]
        if len(usernames) != len(set(usernames)):
            raise ValueError("Usernames must be unique")
        return users

    def get_user_by_chat_id(self, chat_id: int) -> Optional[UserConfig]:
        """Get user configuration by chat ID."""
        for user in self.users:
            if user.chat_id == chat_id:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[UserConfig]:
        """Get user configuration by username."""
        for user in self.users:
            if user.username == username:
                return user
        return None


def load_config(config_path: str = "config/config.yaml") -> Config:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Loaded and validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    # Load environment variables from .env file
    load_dotenv()

    # Load YAML configuration
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    # Substitute environment variables in bot_token
    if "telegram" in config_data and "bot_token" in config_data["telegram"]:
        bot_token = config_data["telegram"]["bot_token"]
        if bot_token.startswith("${") and bot_token.endswith("}"):
            env_var = bot_token[2:-1]
            config_data["telegram"]["bot_token"] = os.getenv(env_var, "")

    # Validate and create config object
    config = Config(**config_data)

    return config
