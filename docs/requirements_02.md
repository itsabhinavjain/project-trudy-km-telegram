# Trudy Telegram - Requirements Specification

## 1. Overview

### 1.1 Purpose
Build a system that allows users to send notes to a Telegram bot and have them automatically organized into daily markdown files with AI-powered processing.

### 1.2 Scope
- Support multiple users (2+ users with different phone numbers)
- Fetch messages from Telegram Bot API
- Download and organize rich media
- Transcribe audio/video content
- Summarize content using AI
- Store notes in Obsidian-compatible markdown format

## 2. Functional Requirements

### 2.1 Message Fetching

**FR-2.1.1**: The system shall use Telegram Bot API (not MTProto)
- **Rationale**: Simpler authentication, bot-specific functionality
- **Implementation**: python-telegram-bot library

**FR-2.1.2**: The system shall fetch messages incrementally
- Only fetch new messages since last run by default
- Support `--full` flag for historical sync
- Track last processed message ID per user

**FR-2.1.3**: The system shall support multiple users
- Each user identified by Telegram chat ID
- Separate processing and storage per user

**FR-2.1.4**: The system shall support automatic user discovery
- **Auto-Discovery Mode**: Automatically detect users who message the bot
- Generate usernames from Telegram username, name, or user ID
- No manual configuration required (optional)
- **Manual Mode**: Optionally configure users explicitly for custom usernames

**FR-2.1.5**: Operations shall be idempotent
- Re-running shall not create duplicates
- Safe to interrupt and resume
- State tracked in JSON file

### 2.2 Message Types

**FR-2.2.1**: Support text messages
- Plain text stored directly in markdown

**FR-2.2.2**: Support image messages
- Download images (JPG, PNG, WebP, etc.)
- Store with original filename or timestamp-based name
- Create wikilinks in markdown
- Include captions as alt text

**FR-2.2.3**: Support video messages
- Download videos (MP4, MOV, etc.)
- Transcribe audio track
- Generate summary
- Store transcript in separate file

**FR-2.2.4**: Support audio messages
- Download audio files and voice messages
- Transcribe content
- Generate summary
- Store transcript separately

**FR-2.2.5**: Support document attachments
- Download PDF, DOCX, etc.
- Create wikilinks (no content extraction initially)

**FR-2.2.6**: Support article links
- Detect non-YouTube HTTP(S) URLs
- Extract article content
- Generate summary
- Store link and summary

**FR-2.2.7**: Support YouTube links
- Detect YouTube URLs (youtube.com, youtu.be)
- Fetch transcript via YouTube API if available
- Download video if transcript unavailable
- Transcribe downloaded video
- Generate summary

### 2.3 Media Processing

**FR-2.3.1**: File naming convention
- Format: `YYYY-MM-DD_HH-MM-SS_original-filename.ext`
- Use original filename from Telegram when available
- Sanitize filename (replace spaces, remove special chars)
- Limit length to 50 characters
- For YouTube: use video title in transcript filename

**FR-2.3.2**: Media organization
- Store in `users/<username>/media/` directory
- Keep media and notes separate
- Use wikilinks for cross-referencing

**FR-2.3.3**: Handle filename collisions
- Append `_1`, `_2`, etc. if filename exists
- Ensure uniqueness

### 2.4 Transcription

**FR-2.4.1**: Use local transcription by default
- Ollama + Whisper model
- Process on macOS locally

**FR-2.4.2**: Audio format handling
- Convert to WAV if needed (using ffmpeg)
- Downsample to 16kHz mono

**FR-2.4.3**: Transcript storage
- Save as separate `.txt` file
- Filename: `YYYY-MM-DD_HH-MM-SS_original-name_transcript.txt`
- Link from markdown with wikilink

**FR-2.4.4**: YouTube transcript preference
- Try YouTube transcript API first
- Fall back to download + transcribe if unavailable
- Configurable via `youtube_prefer_transcript` setting

### 2.5 Summarization

**FR-2.5.1**: Support multiple providers
- Ollama (local models)
- Claude Code CLI (user's subscription)
- Configurable via config file

**FR-2.5.2**: Content-specific prompts
- Different prompts for videos, audio, articles, YouTube
- Customizable in configuration

**FR-2.5.3**: Summary format
- Store inline in markdown file
- Clear "Summary:" header
- Bullet points or paragraphs as appropriate

**FR-2.5.4**: Optional summarization
- `--no-summarize` flag to skip
- `enabled: false` in config
- Processor should work without summarizer

### 2.6 Markdown Output

**FR-2.6.1**: Daily file format
- Filename: `YYYY-MM-DD.md`
- Stored in `users/<username>/notes/`

**FR-2.6.2**: File structure
```markdown
# YYYY-MM-DD

## HH:MM

[Message content]

---

## HH:MM

[Next message]

---
```

**FR-2.6.3**: Timestamp headers
- Format: `## HH:MM` by default
- Configurable format (HH:MM, HH:MM:SS)
- Timezone-aware (convert to local time)

**FR-2.6.4**: Wikilink format
- Obsidian style by default: `![[filename|caption]]`
- Configurable: obsidian or standard markdown
- Embed media with `![[]]`
- Link text files with `[[]]`

**FR-2.6.5**: Content sections
- Type header (e.g., "Video Note", "Article", "Image")
- Media wikilinks
- Transcript links (if applicable)
- Summary (if generated)
- Separator (`---`)

### 2.7 State Management

**FR-2.7.1**: State file structure
```json
{
  "version": "1.0",
  "last_updated": "timestamp",
  "users": {
    "username": {
      "chat_id": 123,
      "first_message_time": "timestamp",
      "last_fetch_time": "timestamp",
      "last_message_id": 456,
      "total_messages": 100
    }
  },
  "statistics": {
    "total_messages_processed": 200,
    "total_media_downloaded": 50,
    "total_transcriptions": 20,
    "total_summaries": 30
  }
}
```

**FR-2.7.2**: State file operations
- Atomic writes using temporary file
- Thread-safe with file locking
- Backup on corruption

**FR-2.7.3**: State tracking
- Update after each message processed
- Not batch updates (for safety)

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-3.1.1**: Concurrent processing
- Support 3-5 concurrent operations (configurable)
- Use asyncio for I/O-bound tasks

**NFR-3.1.2**: Transcription timeout
- Default: 5 minutes per file
- Configurable

**NFR-3.1.3**: API rate limiting
- Respect Telegram API limits
- Implement retry with backoff

### 3.2 Reliability

**NFR-3.2.1**: Error handling
- Skip individual failures by default
- Continue processing remaining messages
- Log all errors with context

**NFR-3.2.2**: Graceful degradation
- If transcription fails, save media without transcript
- If summarization fails, skip summary
- If article extraction fails, save link only

**NFR-3.2.3**: Recovery
- Support interruption and resume
- Idempotent operations
- State persisted after each message

### 3.3 Configurability

**NFR-3.3.1**: Configuration layering
Priority: CLI args > Environment vars > config.yaml > Defaults

**NFR-3.3.2**: Configuration validation
- Validate on load using Pydantic
- Fail fast with clear error messages

### 3.4 Logging

**NFR-3.4.1**: Log levels
- DEBUG: Detailed operation logs
- INFO: Progress and completion
- WARNING: Retries and fallbacks
- ERROR: Failures requiring attention

**NFR-3.4.2**: Log outputs
- Console: Rich formatted, INFO level by default
- File: All logs (DEBUG+), rotated
- Error file: ERROR+ only

**NFR-3.4.3**: Log rotation
- Max size: 10MB
- Keep 5 backup files

### 3.5 Security & Privacy

**NFR-3.5.1**: Credentials
- Bot token in `.env` file (gitignored)
- Never log credentials

**NFR-3.5.2**: File permissions
- Notes/media readable only by user
- State file protected

**NFR-3.5.3**: Local processing
- Transcription local by default (Ollama)
- Summarization configurable (local or Claude)

## 4. Technical Requirements

### 4.1 Technology Stack

**TR-4.1.1**: Language & Runtime
- Python 3.11+
- AsyncIO for concurrency

**TR-4.1.2**: Package Management
- uv for dependency management
- pyproject.toml configuration

**TR-4.1.3**: Key Libraries
- python-telegram-bot: Telegram API
- ollama: Local AI models
- trafilatura: Article extraction
- youtube-transcript-api: YouTube transcripts
- pydantic: Configuration validation
- click: CLI interface
- rich: Terminal output

**TR-4.1.4**: System Dependencies
- FFmpeg: Audio/video conversion
- Ollama: Local AI (optional)
- Whisper: Transcription (via Ollama)

### 4.2 Project Structure

**TR-4.2.1**: Module organization
```
src/
├── core/         # Config, logging, state
├── telegram/     # API client, fetcher, downloader
├── processors/   # Message type processors
├── ai/           # Transcription, summarization
├── markdown/     # Formatting, writing
└── utils/        # Helpers
```

**TR-4.2.2**: Processor architecture
- Plugin-based design
- Each processor implements base interface
- Auto-detection based on message type

### 4.3 Data Storage

**TR-4.3.1**: Directory structure
```
data/
├── state.json
└── users/
    └── <username>/
        ├── notes/      # YYYY-MM-DD.md
        └── media/      # All media files
```

**TR-4.3.2**: File formats
- Notes: Markdown (.md)
- Transcripts: Plain text (.txt)
- State: JSON (.json)
- Media: Original formats

## 5. User Interface Requirements

### 5.1 Command Line Interface

**UIR-5.1.1**: Primary command
```bash
uv run trudy [OPTIONS]
```

**UIR-5.1.2**: Options
- `--config PATH`: Config file path
- `--full`: Fetch all messages
- `--user USERNAME`: Process specific user
- `--dry-run`: Preview mode
- `--no-summarize`: Skip summaries
- `--verbose`: Debug logging

**UIR-5.1.3**: Output format
- Progress bars for processing
- Summary statistics at end
- Color-coded status messages
- Clear error messages

### 5.2 Configuration Interface

**UIR-5.2.1**: YAML configuration file
- Human-readable
- Well-commented
- Example file provided

**UIR-5.2.2**: Environment variables
- `.env` for secrets
- `.env.example` provided

## 6. Quality Requirements

### 6.1 Testability

**QR-6.1.1**: Unit tests
- Test processors with mock messages
- Test state management
- Test file utilities

**QR-6.1.2**: Integration tests
- End-to-end pipeline tests
- Mock Telegram API
- Verify idempotency

### 6.2 Maintainability

**QR-6.2.1**: Code organization
- Clear module separation
- DRY principles
- Type hints throughout

**QR-6.2.2**: Documentation
- README.md: Overview and quick start
- USAGE.md: Detailed guide
- requirements.md: This file
- Docstrings on all classes/functions

### 6.3 Extensibility

**QR-6.3.1**: Future features
- Designed for future slash command support
- Ready for bot-initiated messages
- Supports future insight generation

**QR-6.3.2**: Plugin architecture
- Easy to add new processors
- Easy to add new AI providers

## 7. Constraints

### 7.1 Platform

**C-7.1.1**: Primary platform
- macOS (user's development environment)
- Should work on Linux

**C-7.1.2**: Telegram limitations
- Bot API file size limit: 20MB
- Rate limits apply

### 7.2 Dependencies

**C-7.2.1**: Required
- Python 3.11+
- uv
- FFmpeg

**C-7.2.2**: Optional
- Ollama (can use Claude instead)
- Claude Code CLI (can use Ollama instead)

## 8. Acceptance Criteria

### 8.1 Core Functionality

- [ ] Fetch messages from Telegram bot
- [ ] Download media files
- [ ] Create daily markdown files
- [ ] Organize by user
- [ ] Incremental fetching works
- [ ] `--full` flag fetches all messages
- [ ] Idempotent operation (no duplicates on re-run)

### 8.2 Message Processing

- [ ] Text messages appear in markdown
- [ ] Images download and link correctly
- [ ] Videos download, transcribe, and summarize
- [ ] Audio transcribes and summarizes
- [ ] Articles extract and summarize
- [ ] YouTube videos fetch transcripts
- [ ] Documents download and link

### 8.3 AI Features

- [ ] Whisper transcription works
- [ ] Ollama summarization works
- [ ] Claude Code CLI summarization works
- [ ] Configurable AI providers
- [ ] Can disable AI features

### 8.4 Output Quality

- [ ] Markdown files well-formatted
- [ ] Wikilinks work in Obsidian
- [ ] Timestamps correct in local timezone
- [ ] Filenames follow naming convention
- [ ] Summaries are helpful and accurate

### 8.5 Reliability

- [ ] State file tracks progress correctly
- [ ] Can interrupt and resume
- [ ] Errors logged properly
- [ ] Failed items logged, processing continues
- [ ] No data loss on interruption

## 9. Out of Scope (for v1.0)

The following features are documented but not implemented in initial version:

- Slash commands for tagging notes
- Bot-initiated messages
- Automated insight generation
- OCR for images
- Document text extraction
- Web interface
- Mobile app
- Real-time sync
- Conflict resolution for multiple devices
- Advanced search features
- Note editing capabilities
- Integration with other note apps (besides Obsidian)

These may be added in future versions based on user feedback and requirements.
