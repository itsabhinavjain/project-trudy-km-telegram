# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trudy is a Telegram bot-based note-taking system that automatically fetches messages from a Telegram bot, processes them (transcription, summarization, media download), and organizes them into daily markdown files. It's designed for personal knowledge management and integrates with Obsidian.

## Essential Commands

### Development & Testing
```bash
# Install dependencies
uv sync

# Run the application (incremental sync)
uv run trudy

# Full sync of all historical messages
uv run trudy --full

# List all discovered users without processing
uv run trudy --discover-users

# Process specific user only
uv run trudy --user <username>

# Dry run (preview without writing files)
uv run trudy --dry-run

# Skip summarization (faster)
uv run trudy --no-summarize

# Verbose logging for debugging
uv run trudy -v

# Run tests
pytest

# Code formatting
black src/ tests/
ruff check src/ tests/

# Type checking
mypy src/
```

### System Dependencies
```bash
# macOS
brew install ffmpeg
brew install ollama  # For local AI

# Pull AI models
ollama pull whisper  # For transcription
ollama pull llama2   # For summarization
```

## Architecture

### Core Data Flow

1. **Message Fetching** (`src/telegram/fetcher.py`):
   - Connects to Telegram Bot API via `TelegramClient`
   - Supports two modes:
     - **Auto-discovery mode** (default): Automatically discovers users who message the bot
     - **Manual mode**: Uses pre-configured users from config.yaml
   - Implements incremental sync using `StateManager` to track last processed message ID per user
   - Returns `Message` objects (simplified from Telegram's message format)

2. **Message Processing** (`src/processors/`):
   - **Processor Chain Pattern**: Each message is evaluated by processors in order until one can handle it
   - Processors inherit from `BaseProcessor` with `can_process()` and `process()` methods
   - Processor types:
     - `TextProcessor`: Plain text messages
     - `MediaProcessor`: Images/photos
     - `AudioVideoProcessor`: Audio/video files with transcription
     - `LinkProcessor`: Article URLs with content extraction
     - `YouTubeProcessor`: YouTube links with transcript fetching
   - Each processor returns a `ProcessedResult` with markdown content and metadata

3. **AI Components** (`src/ai/`):
   - **Transcriber** (`transcriber.py`): Uses Ollama Whisper for audio/video transcription
   - **Summarizer** (abstract base in `summarizer.py`):
     - `OllamaSummarizer`: Uses local Ollama models (llama2, mistral, etc.)
     - `ClaudeSummarizer`: Uses Claude Code CLI for higher quality summaries
   - Both are pluggable via configuration

4. **Markdown Output** (`src/markdown/`):
   - `MarkdownWriter`: Appends entries to daily markdown files (e.g., `2026-01-03.md`)
   - `MarkdownFormatter`: Formats timestamps and wikilinks (Obsidian-compatible)
   - Files organized by user: `data/users/<username>/notes/<date>.md`

5. **State Management** (`src/core/state.py`):
   - **Persistent State**: Tracks processing state in `data/state.json`
   - **Per-User Tracking**: Stores last_message_id, total_messages, first_message_time, last_fetch_time
   - **User Discovery**: Accumulates discovered users across all runs (never forgets users)
   - Enables idempotent operations and incremental sync

### Key Design Patterns

- **Processor Chain**: Processors are tried in sequence until one matches
- **Dependency Injection**: Configuration and dependencies passed through constructors
- **Async/Await**: All I/O operations are async (Telegram API, file operations, AI calls)
- **Pydantic Models**: Configuration validated with pydantic BaseModel
- **State Persistence**: JSON-based state tracking for incremental operations

### Important Architectural Decisions

1. **Auto-Discovery vs Manual Configuration**:
   - Default is auto-discovery (users: [] in config.yaml)
   - System automatically generates usernames from Telegram metadata
   - State file accumulates all discovered users across runs
   - Manual configuration available for custom usernames or filtering

2. **Media Storage**:
   - Downloaded media stored in `data/users/<username>/media/`
   - Filenames: `YYYY-MM-DD_HH-MM-SS_<description>.<ext>`
   - Transcripts saved as separate .txt files alongside media
   - Wikilinks in markdown reference media files relatively

3. **AI Provider Flexibility**:
   - Transcription: Ollama Whisper (local) or remote API
   - Summarization: Ollama models or Claude Code CLI
   - YouTube: Prefer transcript API, fallback to download+transcribe
   - All configurable via `config/config.yaml`

## Configuration

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Required. Get from @BotFather on Telegram
- Set in `.env` file (copy from `.env.example`)

### Config File (`config/config.yaml`)
- **telegram**: Bot token, API settings, retry behavior
- **users**: Leave empty `[]` for auto-discovery, or manually configure
- **transcription**: Enable/disable, provider (ollama/remote), model settings
- **summarization**: Enable/disable, provider (ollama/claude), prompts
- **storage**: Base directory, subdirectory names
- **processing**: Concurrency limits, error handling
- **markdown**: Timezone, timestamp format, wikilink style

## Common Development Tasks

### Adding a New Message Processor

1. Create new processor in `src/processors/<name>.py`
2. Inherit from `BaseProcessor`
3. Implement `can_process(message: Message) -> bool`
4. Implement `process(message, media_dir, notes_dir) -> ProcessedResult`
5. Register in `src/main.py` processor list (order matters!)

Example:
```python
class MyProcessor(BaseProcessor):
    async def can_process(self, message: Message) -> bool:
        return message.message_type == "my_type"

    async def process(self, message, media_dir, notes_dir):
        # Process message
        return ProcessedResult(markdown_content="...", ...)
```

### Adding a New AI Summarizer

1. Create new summarizer in `src/ai/<name>_summarizer.py`
2. Inherit from `BaseSummarizer` (in `src/ai/summarizer.py`)
3. Implement `summarize(content: str, prompt: str) -> str`
4. Add configuration to `SummarizationConfig` in `src/core/config.py`
5. Register in `src/main.py` based on config.summarization.provider

### Modifying Message Fetching Logic

- Main logic in `MessageFetcher.fetch_and_discover_users()` (`src/telegram/fetcher.py`)
- User discovery: `generate_username_from_telegram()` function
- Message conversion: `Message.from_telegram_message()` classmethod
- State tracking: `StateManager.update_user_state()` after processing

### Testing Notes

- Test files in `tests/` directory
- Use `pytest-asyncio` for async tests
- Mock Telegram API responses using fixtures
- State file should be mocked/isolated in tests

## Data Structures

### Message Object
Simplified representation of Telegram messages with:
- Basic fields: message_id, chat_id, user_id, username, timestamp
- Content: text, caption
- Media: file_id, file_name, file_size, mime_type
- Type: text, video, audio, voice, image, photo, document, link

### ProcessedResult
Output from message processors containing:
- markdown_content: Formatted markdown string
- media_files: List of downloaded file paths
- transcript_file: Path to transcript (if applicable)
- summary: AI-generated summary text
- metadata: Additional processor-specific data

### State Structure
Persisted in `data/state.json`:
```json
{
  "users": {
    "username": {
      "chat_id": 123,
      "phone": "+1234567890",
      "last_message_id": 456,
      "total_messages": 100,
      "first_message_time": "2026-01-01T10:00:00",
      "last_fetch_time": "2026-01-03T20:00:00"
    }
  },
  "statistics": {
    "total_messages": 100,
    "total_media": 50,
    "total_transcriptions": 20,
    "total_summaries": 30
  }
}
```

## Important Files

- `src/main.py`: CLI entry point and main orchestration logic
- `src/core/config.py`: Pydantic configuration models and YAML loading
- `src/core/state.py`: State persistence and user tracking
- `src/telegram/fetcher.py`: Message fetching and user auto-discovery
- `src/telegram/client.py`: Low-level Telegram Bot API wrapper
- `src/telegram/downloader.py`: Media file downloading
- `src/processors/base.py`: Base processor interface
- `src/ai/transcriber.py`: Audio/video transcription via Ollama
- `src/ai/summarizer.py`: Base summarizer interface
- `src/markdown/writer.py`: Daily markdown file management

## Debugging Tips

1. **Use verbose mode**: `uv run trudy -v` enables DEBUG logging
2. **Check logs**: `logs/trudy.log` (general) and `logs/errors.log` (errors)
3. **Inspect state**: `data/state.json` shows last processed message IDs
4. **Dry run**: `uv run trudy --dry-run` to preview without side effects
5. **Test Telegram connection**: Send message to bot, check with `--discover-users`
6. **Ollama issues**: Verify with `ollama list` and `curl http://localhost:11434/api/tags`
