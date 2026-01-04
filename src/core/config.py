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


class StagingRetentionConfig(BaseModel):
    """Staging file retention policy configuration."""

    policy: Literal["keep_all", "keep_days", "delete_after_process"] = Field(
        default="keep_days", description="Retention policy for staging files"
    )
    days: int = Field(default=7, description="Days to keep staging files (used with keep_days policy)")


class StorageConfig(BaseModel):
    """Storage paths configuration."""

    base_dir: str = Field(default="./data", description="Base data directory")
    staging_dir: str = Field(default="staging", description="Staging directory name")
    processed_dir: str = Field(default="processed", description="Processed directory name")
    media_dir: str = Field(default="media", description="Media directory name")
    staging_retention: StagingRetentionConfig = Field(
        default_factory=StagingRetentionConfig, description="Staging retention policy"
    )

    @property
    def base_path(self) -> Path:
        """Get base directory as Path object."""
        return Path(self.base_dir).resolve()

    def get_staging_dir(self, username: str) -> Path:
        """Get staging directory for a specific user."""
        return self.base_path / self.staging_dir / username

    def get_processed_dir(self, username: str) -> Path:
        """Get processed directory for a specific user."""
        return self.base_path / self.processed_dir / username

    def get_media_dir(self, username: str) -> Path:
        """Get shared media directory for a specific user."""
        return self.base_path / self.media_dir / username

    # Keep old methods for backward compatibility during migration
    def get_user_notes_dir(self, username: str) -> Path:
        """Get notes directory for a specific user (deprecated: use get_processed_dir)."""
        return self.get_processed_dir(username)

    def get_user_media_dir(self, username: str) -> Path:
        """Get media directory for a specific user (deprecated: use get_media_dir)."""
        return self.get_media_dir(username)


class TesseractConfig(BaseModel):
    """Tesseract OCR configuration."""

    languages: list[str] = Field(default=["eng"], description="OCR languages")
    config: str = Field(default="--psm 3", description="Tesseract config options")


class CloudOCRConfig(BaseModel):
    """Cloud OCR provider configuration."""

    provider: Literal["google_vision", "azure", "aws"] = Field(
        default="google_vision", description="Cloud OCR provider"
    )
    api_key: str = Field(default="", description="API key for cloud provider")


class OCRConfig(BaseModel):
    """OCR configuration."""

    enabled: bool = Field(default=True, description="Enable OCR")
    provider: Literal["tesseract", "cloud"] = Field(
        default="tesseract", description="OCR provider"
    )
    tesseract: TesseractConfig = Field(default_factory=TesseractConfig)
    cloud: CloudOCRConfig = Field(default_factory=CloudOCRConfig)


class LinkExtractFields(BaseModel):
    """Link metadata fields to extract."""

    title: bool = Field(default=True, description="Extract page title")
    description: bool = Field(default=True, description="Extract meta description")
    opengraph: bool = Field(default=False, description="Extract OpenGraph metadata")
    favicon: bool = Field(default=False, description="Extract favicon URL")


class LinkExtractionConfig(BaseModel):
    """Link metadata extraction configuration."""

    enabled: bool = Field(default=True, description="Enable link metadata extraction")
    timeout: int = Field(default=10, description="HTTP request timeout in seconds")
    user_agent: str = Field(
        default="Trudy/2.0 (Personal Knowledge Bot)",
        description="User agent for HTTP requests"
    )
    extract: LinkExtractFields = Field(default_factory=LinkExtractFields)


class TaggingRule(BaseModel):
    """Rule for automatic tag generation."""

    pattern: str = Field(..., description="Regex pattern to match")
    tag: str = Field(..., description="Tag to apply when pattern matches")


class AITaggingConfig(BaseModel):
    """AI-based tagging configuration."""

    enabled: bool = Field(default=False, description="Enable AI-based tagging")
    provider: Literal["ollama"] = Field(default="ollama", description="AI provider")
    model: str = Field(default="llama2", description="Model name")
    max_tags: int = Field(default=5, description="Maximum tags to generate")
    prompt: str = Field(
        default="Generate 3-5 relevant hashtags for this message. Return only hashtags separated by commas.",
        description="Prompt for AI tagging"
    )


class TaggingConfig(BaseModel):
    """Auto-tagging configuration."""

    enabled: bool = Field(default=True, description="Enable auto-tagging")
    rules: list[TaggingRule] = Field(
        default_factory=lambda: [
            TaggingRule(pattern="screenshot", tag="#screenshot"),
            TaggingRule(pattern="meeting", tag="#meeting"),
            TaggingRule(pattern="reminder|remind", tag="#reminder"),
            TaggingRule(pattern="todo|task", tag="#task"),
            TaggingRule(pattern=r"\.pdf$", tag="#document"),
            TaggingRule(pattern=r"youtube\.com|youtu\.be", tag="#youtube"),
            TaggingRule(pattern="image|photo", tag="#image"),
            TaggingRule(pattern="video", tag="#video"),
            TaggingRule(pattern="audio|voice", tag="#audio"),
        ],
        description="Rule-based tagging patterns"
    )
    ai_tagging: AITaggingConfig = Field(
        default_factory=AITaggingConfig, description="AI-based tagging config"
    )


class ProcessingConfig(BaseModel):
    """Processing configuration."""

    max_workers: int = Field(default=3, description="Number of parallel processing workers")
    skip_errors: bool = Field(
        default=True, description="Continue processing on individual errors"
    )
    retry_failed: bool = Field(default=True, description="Retry failed messages")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    show_progress: bool = Field(default=True, description="Show progress bars")
    report_interval: int = Field(default=10, description="Progress report interval (messages)")


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

    timezone: str = Field(default="America/New_York", description="Timezone for timestamps")
    timestamp_format: str = Field(default="HH:mm", description="Time format for headers")
    date_format: str = Field(default="YYYY-MM-DD", description="Date format for files")
    wikilink_style: Literal["obsidian", "markdown"] = Field(
        default="obsidian", description="Wikilink style for media references"
    )
    include_message_id: bool = Field(
        default=False, description="Include Telegram message ID in processed markdown"
    )
    include_edit_history: bool = Field(
        default=True, description="Track message edit history in processed markdown"
    )


class Config(BaseModel):
    """Main configuration."""

    telegram: TelegramConfig
    users: list[UserConfig] = Field(
        default_factory=list,
        description="Auto-discovery mode: Leave empty for automatic user discovery.",
    )
    storage: StorageConfig = Field(default_factory=StorageConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    summarization: SummarizationConfig = Field(default_factory=SummarizationConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    links: LinkExtractionConfig = Field(default_factory=LinkExtractionConfig)
    tagging: TaggingConfig = Field(default_factory=TaggingConfig)
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

    # Substitute environment variables
    # Telegram bot token
    if "telegram" in config_data and "bot_token" in config_data["telegram"]:
        bot_token = config_data["telegram"]["bot_token"]
        if bot_token.startswith("${") and bot_token.endswith("}"):
            env_var = bot_token[2:-1]
            config_data["telegram"]["bot_token"] = os.getenv(env_var, "")

    # OCR API key
    if "ocr" in config_data and "cloud" in config_data["ocr"]:
        if "api_key" in config_data["ocr"]["cloud"]:
            api_key = config_data["ocr"]["cloud"]["api_key"]
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                config_data["ocr"]["cloud"]["api_key"] = os.getenv(env_var, "")

    # Validate and create config object
    config = Config(**config_data)

    return config
