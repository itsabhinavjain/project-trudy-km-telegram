# CLAUDE.md - Trudy 2.0

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trudy 2.0 is a Telegram bot-based personal knowledge management system that transforms messages into organized, enriched markdown notes. It features a **two-phase architecture** that separates message fetching from processing, enabling atomic operations, checksum-based reprocessing, and flexible AI enrichment.

**Version:** 2.0.0
**Architecture:** Two-phase (Fetch → Staging, Staging → Processed)
**CLI Framework:** Typer with Rich formatting
**AI Features:** Transcription, Summarization, OCR, Auto-tagging

---

## Essential Commands (v2.0)

### Core Workflow Commands
```bash
# Install dependencies
uv sync

# MOST COMMON: Full sync (fetch + process)
uv run trudy sync

# Fetch messages from Telegram to staging
uv run trudy fetch

# Process staging files to enriched markdown
uv run trudy process

# Sync specific users
uv run trudy sync --user alice --user bob

# Full historical sync
uv run trudy sync --full

# Quick sync without AI features (faster)
uv run trudy sync --skip-transcription --skip-ocr --skip-summarization

# Verbose mode for debugging
uv run trudy sync -v

# Dry run (preview without writing)
uv run trudy fetch --dry-run
uv run trudy process --dry-run
```

### Get Help
```bash
# General help
uv run trudy --help

# Command-specific help
uv run trudy fetch --help
uv run trudy process --help
uv run trudy sync --help
```

### Development Commands
```bash
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
brew install tesseract  # For OCR
brew install ollama      # For local AI

# Pull AI models
ollama pull whisper  # For transcription
ollama pull llama2   # For summarization
```

---

## Two-Phase Architecture

Trudy 2.0 uses a **two-phase workflow** that separates fetching from processing:

```
Phase 1: Fetch → Staging        Phase 2: Staging → Processed
┌─────────────┐                 ┌─────────────┐
│  Telegram   │                 │   Staging   │
│   Bot API   │                 │   Files     │
└──────┬──────┘                 └──────┬──────┘
       │                               │
       ├─ Auto-discover users          ├─ Parse staging markdown
       ├─ Fetch new messages           ├─ Run through processor chain
       ├─ Download media               ├─ Apply AI features:
       │  (to shared media/)            │  - Transcription
       ├─ Write to staging/             │  - OCR
       │  (simple format)               │  - Summarization
       └─ Update fetch_state            │  - Auto-tagging
                                        ├─ Extract link metadata
                                        ├─ Write to processed/
                                        │  (rich YAML format)
                                        └─ Update process_state
```

### Why Two Phases?

1. **Atomic Operations**: Fetch and process can fail independently
2. **Reprocessing**: Change AI models/prompts and reprocess without re-fetching
3. **Checksum-based Updates**: Only reprocess when staging files change
4. **Performance**: Skip expensive AI operations when not needed
5. **Debugging**: Inspect staging files before processing

---

## Directory Structure (v2.0)

```
data/
├── staging/              # Phase 1 output: Raw messages (simple format)
│   ├── alice/
│   │   ├── 2026-01-04.md
│   │   └── 2026-01-05.md
│   └── bob/
│       └── 2026-01-04.md
│
├── processed/            # Phase 2 output: Enriched markdown (YAML metadata)
│   ├── alice/
│   │   ├── 2026-01-04.md
│   │   └── 2026-01-05.md
│   └── bob/
│       └── 2026-01-04.md
│
├── media/                # Shared media folder (all users)
│   ├── alice/
│   │   ├── 2026-01-04_14-30-15_image.jpg
│   │   ├── 2026-01-04_15-20-10_video.mp4
│   │   └── 2026-01-04_15-20-10_video_transcript.txt
│   └── bob/
│       └── 2026-01-04_10-15-30_document.pdf
│
└── state.json            # Dual-state tracking (fetch + process states)
```

---

## Markdown Formats

### Staging Format (Simple)
Written by `StagingWriter` in Phase 1. Designed to be:
- **Raw**: Verbatim text in headers
- **Minimal**: No metadata, just content
- **Human-readable**: Easy to scan

```markdown
## 14:30 - Hello, this is a test message

Hello, this is a test message

---

## 14:35 - [Image]

![Image](../media/alice/2026-01-04_14-35-20_image.jpg)

Caption: Beautiful sunset

---

## 14:40 - https://example.com/article

https://example.com/article

---
```

### Processed Format (Rich YAML)
Written by `ProcessedWriter` in Phase 2. Includes:
- **Type**: Message type classification
- **Content**: Full text or media references
- **AI Results**: Transcripts, summaries, OCR text
- **Tags**: Auto-generated hashtags
- **Links**: Extracted metadata (title, description)
- **Context**: Reply-to, forwarded-from, edits

```markdown
## 14:30 - Hello, this is a test message
type: text
content: |-
  Hello, this is a test message
tags: [#greeting]

---

## 14:35 - [Image]
type: image
file: ![[2026-01-04_14-35-20_image.jpg]]
caption: |-
  Beautiful sunset
ocr_text: |-
  SUNSET BEACH
  PHOTOGRAPHY BY ALICE
tags: [#image, #ocr]

---

## 14:40 - https://example.com/article
type: link
content: |-
  https://example.com/article
links:
  - url: "https://example.com/article"
    title: "How to Build Better Software"
    description: "A comprehensive guide to software architecture"
summary: |-
  The article discusses software architecture patterns...
tags: [#link, #article, #summarized]

---
```

---

## State Management (Dual-State)

State file: `data/state.json`

### Structure
```json
{
  "users": {
    "alice": {
      "chat_id": 123456789,
      "phone": null,
      "first_seen": "2026-01-04T10:00:00",
      "last_seen": "2026-01-05T15:30:00",

      "fetch_state": {
        "last_message_id": 4567,
        "last_fetch_time": "2026-01-05T15:30:00",
        "total_messages_fetched": 150
      },

      "process_state": {
        "last_processed_date": "2026-01-05",
        "last_process_time": "2026-01-05T16:00:00",
        "total_messages_processed": 148,
        "file_checksums": {
          "data/staging/alice/2026-01-04.md": "a1b2c3d4...",
          "data/staging/alice/2026-01-05.md": "e5f6g7h8..."
        },
        "pending_files": [
          "data/staging/alice/2026-01-06.md"
        ]
      }
    }
  },

  "statistics": {
    "total_messages_fetched": 150,
    "total_messages_processed": 148,
    "total_transcriptions": 12,
    "total_ocr_performed": 8,
    "total_summaries": 25
  }
}
```

### Key Concepts

- **FetchState**: Tracks what was fetched from Telegram (last_message_id)
- **ProcessState**: Tracks what was processed (checksums, pending files)
- **Checksums**: SHA-256 hashes detect when staging files change
- **Pending Files**: List of staging files waiting to be processed
- **Auto-backup**: State is backed up before every write

---

## Core Components

### 1. CLI Layer (`src/cli/`)

**Framework:** Typer with Rich formatting

**Commands:**
- `fetch`: Phase 1 - Fetch messages to staging
- `process`: Phase 2 - Process staging to enriched markdown
- `sync`: Combined fetch + process (most common)

**Key Files:**
- `main.py`: Typer app entry point, global options
- `fetch.py`: Fetch command implementation
- `process.py`: Process command implementation
- `sync.py`: Combined sync workflow

### 2. Fetching Layer (`src/telegram/`)

**Responsibilities:**
- Connect to Telegram Bot API
- Auto-discover users
- Fetch new messages (incremental sync)
- Download media to shared `media/` folder
- Write to staging area
- Update `fetch_state`

**Key Files:**
- `fetcher.py`: `MessageFetcher` class, auto-discovery
- `client.py`: Low-level Telegram Bot API wrapper
- `downloader.py`: Media file downloading

**Important Classes:**
- `Message`: Simplified message representation (dataclass)
- `MessageFetcher`: Main fetching orchestration

### 3. Processing Layer (`src/core/`, `src/processors/`)

**Responsibilities:**
- Read pending staging files
- Calculate checksums (detect changes)
- Parse staging markdown into `Message` objects
- Run through processor chain
- Apply AI features (OCR, tagging)
- Write to processed area with YAML metadata
- Update `process_state`

**Key Files:**
- `processor.py`: `MessageProcessor` orchestration
- `processors/base.py`: `BaseProcessor`, `ProcessedResult`
- `processors/text.py`: Text message processor
- `processors/media.py`: Image/document processor (with OCR)
- `processors/link.py`: Article link processor (with metadata)
- `processors/audio_video.py`: Audio/video processor (with transcription)
- `processors/youtube.py`: YouTube link processor

**Processor Chain Pattern:**
Processors are tried in order until one can handle the message:
```python
processors = [
    YouTubeProcessor,    # First (most specific)
    LinkProcessor,       # Article links
    AudioVideoProcessor, # Audio/video with transcription
    MediaProcessor,      # Images/documents with OCR
    TextProcessor,       # Fallback (most generic)
]
```

### 4. AI Components (`src/ai/`)

**OCR (`ocr.py`):**
- `OCRManager`: Unified OCR interface
- `TesseractOCR`: Local Tesseract integration
- `CloudOCR`: Placeholder for Google Vision, Azure, AWS

**Tagging (`tagger.py`):**
- `Tagger`: Main tagging interface
- `RuleBasedTagger`: Regex pattern matching
- `AITagger`: LLM-based tagging (placeholder)

**Transcription (`transcriber.py`):**
- Ollama Whisper integration (existing)

**Summarization (`summarizer.py`):**
- `OllamaSummarizer`: Local models
- `ClaudeSummarizer`: Claude Code CLI

### 5. Markdown Layer (`src/markdown/`)

**Writers:**
- `staging_writer.py`: Simple format for staging
- `processed_writer.py`: Rich YAML format for processed

**Readers:**
- `staging_reader.py`: Parse staging markdown → `Message` objects

**Utilities:**
- `formatter.py`: `MarkdownFormatter` class, wikilinks, timestamps

### 6. State Management (`src/core/state.py`)

**Classes:**
- `FetchState`: Tracks fetching progress
- `ProcessState`: Tracks processing progress, checksums
- `UserState`: Combines fetch + process states
- `StateManager`: Load/save/update state

**Key Methods:**
```python
# Fetching
state_manager.update_fetch_state(username, last_message_id, count)
state_manager.add_pending_file(username, staging_file)

# Processing
state_manager.get_pending_files(username) -> List[str]
state_manager.mark_file_processed(username, file, checksum, count)
state_manager.get_file_checksum(username, file) -> Optional[str]
```

### 7. Configuration (`src/core/config.py`)

**Pydantic Models:**
- `Config`: Root configuration
- `TelegramConfig`: Bot token, API settings
- `StorageConfig`: Directory paths, retention policies
- `MarkdownConfig`: Timezone, formats, wikilink style
- `OCRConfig`: OCR provider settings
- `TaggingConfig`: Tagging rules, AI settings
- `TranscriptionConfig`: Transcription settings
- `SummarizationConfig`: Summarization settings

**Important Methods:**
```python
config.storage.get_staging_dir(username) -> Path
config.storage.get_processed_dir(username) -> Path
config.storage.get_media_dir(username) -> Path
```

---

## Data Structures

### Message (Enhanced for v2.0)
```python
@dataclass
class Message:
    message_id: int
    chat_id: int
    user_id: int
    username: str
    timestamp: datetime
    message_type: str  # text, image, video, audio, voice, document, link
    text: Optional[str]
    caption: Optional[str]
    file_id: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
```

### ProcessedResult (Enhanced for v2.0)
```python
@dataclass
class ProcessedResult:
    markdown_content: str        # For backward compatibility
    message_type: str            # NEW: Message type
    media_files: List[Path]
    transcript_file: Optional[Path]
    summary: Optional[str]
    tags: List[str]              # NEW: Auto-generated tags
    links: List[Dict]            # NEW: Extracted link metadata
    ocr_text: Optional[str]      # NEW: OCR text from images
    reply_to: Optional[Dict]     # NEW: Reply context (Phase 6)
    forwarded_from: Optional[Dict]  # NEW: Forward context (Phase 6)
    edited_at: Optional[datetime]   # NEW: Edit timestamp (Phase 6)
    metadata: Dict
```

### ProcessingReport
```python
@dataclass
class ProcessingReport:
    users_processed: int
    files_processed: int
    messages_processed: int
    messages_skipped: int
    transcriptions: int
    ocr_performed: int
    summaries_generated: int
    tags_generated: int
    links_extracted: int
    errors: int
    error_details: List[str]
    time_elapsed: float
```

---

## Common Development Tasks

### 1. Adding a New Processor

Create `src/processors/mytype.py`:
```python
from src.processors.base import BaseProcessor, ProcessedResult

class MyTypeProcessor(BaseProcessor):
    async def can_process(self, message: Message) -> bool:
        return message.message_type == "my_type"

    async def process(self, message, media_dir, notes_dir):
        # Process message
        return ProcessedResult(
            markdown_content="...",
            message_type="my_type",
            tags=["#my_type"],
            metadata={},
        )
```

Register in the main initialization code (when creating processor list).

### 2. Adding a New CLI Command

Create `src/cli/mycommand.py`:
```python
import typer
from rich.console import Console

console = Console()

def mycommand_cmd(
    ctx: typer.Context,
    option: str = typer.Option("default", help="Example option"),
):
    """My command description."""
    config_path = ctx.obj.get("config_path")
    # Implementation
    console.print("[green]Success![/green]")
```

Register in `src/cli/main.py`:
```python
from src.cli.mycommand import mycommand_cmd
app.command(name="mycommand")(mycommand_cmd)
```

### 3. Modifying Staging Format

Edit `src/markdown/staging_writer.py`:
- `_format_header()`: Change header format
- `_format_content()`: Change content format

Also update `src/markdown/staging_reader.py`:
- `_parse_entry()`: Parse the new format

### 4. Modifying Processed Format

Edit `src/markdown/processed_writer.py`:
- `_format_metadata()`: Add new YAML fields

### 5. Adding a New Tagging Rule

Edit `config/config.yaml`:
```yaml
tagging:
  enabled: true
  rules:
    - pattern: "my_pattern"
      tag: "#my_tag"
```

### 6. Reprocessing with New Settings

```bash
# Change config (e.g., new summarization prompt)
# Then force reprocess all files
uv run trudy process --reprocess

# Or reprocess specific user
uv run trudy process --user alice --reprocess
```

---

## Testing Strategy

### Unit Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_staging_writer.py

# Run with coverage
pytest --cov=src tests/
```

### Integration Testing
```bash
# Test full workflow with dry-run
uv run trudy sync --dry-run --verbose

# Test fetch only
uv run trudy fetch --dry-run

# Test process only
uv run trudy process --dry-run
```

### Test Data Locations
- Test config: `tests/fixtures/config.yaml`
- Mock state: Use `StateManager` with temp file
- Mock Telegram: Use `pytest` fixtures

---

## Debugging Tips

### 1. Verbose Mode
```bash
# See DEBUG logs
uv run trudy sync -v
```

### 2. Check State
```bash
# Inspect state file
cat data/state.json | jq

# Check specific user
cat data/state.json | jq '.users.alice'

# Check pending files
cat data/state.json | jq '.users.alice.process_state.pending_files'
```

### 3. Inspect Staging Files
```bash
# View staging file
cat data/staging/alice/2026-01-04.md

# Check if file has changed
sha256sum data/staging/alice/2026-01-04.md
```

### 4. Test Individual Phases
```bash
# Test fetch only
uv run trudy fetch --user alice --dry-run -v

# Test process only
uv run trudy process --user alice --dry-run -v
```

### 5. Common Issues

**Circular Import Errors:**
- Use `TYPE_CHECKING` and quoted type hints
- Example in `src/telegram/downloader.py`

**OCR Not Working:**
```bash
# Check Tesseract installation
tesseract --version

# Test OCR manually
tesseract test.jpg stdout
```

**Ollama Issues:**
```bash
# Check Ollama is running
ollama list

# Test API
curl http://localhost:11434/api/tags
```

**State Corruption:**
- State is backed up automatically
- Check `data/state.json.backup`
- Delete state to reset (loses tracking)

---

## Architecture Diagrams

### Phase 1: Fetch → Staging
```
Telegram API
    ↓
MessageFetcher
    ├─ Auto-discover users
    ├─ Fetch new messages
    ├─ Download media (MediaDownloader)
    └─ Write to staging (StagingWriter)
         ↓
    data/staging/
    data/media/
    Update fetch_state
```

### Phase 2: Staging → Processed
```
data/staging/
    ↓
MessageProcessor
    ├─ Read pending files (StagingReader)
    ├─ Check checksums
    ├─ Process messages:
    │   ├─ Processor chain
    │   ├─ OCR (images)
    │   ├─ Transcription (audio/video)
    │   ├─ Summarization
    │   └─ Tagging
    └─ Write to processed (ProcessedWriter)
         ↓
    data/processed/
    Update process_state
```

---

## Configuration Reference

See `config/config.yaml` for complete configuration.

**Key Sections:**
- `telegram`: Bot token, API settings
- `storage`: Directory paths, retention policies
- `markdown`: Timezone, formats, wikilink style
- `ocr`: OCR provider (tesseract/cloud)
- `tagging`: Auto-tagging rules
- `transcription`: Whisper settings
- `summarization`: Provider, prompts
- `processing`: Workers, error handling

---

## Migration from v1.x

**Breaking Changes:**
- CLI changed from Click to Typer
- Commands changed: `trudy --full` → `trudy sync --full`
- Directory structure changed: `data/users/` → `data/staging/`, `data/processed/`, `data/media/`
- State structure changed: Added `fetch_state` and `process_state`

**Not Backward Compatible:**
- v2.0 requires starting fresh (no migration path)
- Old data in `data/users/` should be backed up separately

---

## Version History

**v2.0.0** (2026-01-05):
- Two-phase architecture (Fetch → Staging, Staging → Processed)
- Typer-based CLI with Rich formatting
- Dual-state management with checksums
- OCR support (Tesseract)
- Auto-tagging (rule-based + AI-ready)
- Link metadata extraction
- Shared media folder
- Reprocessing without re-fetching

**v1.x** (Legacy):
- Single-phase architecture
- Click-based CLI
- Simple state management
- Basic markdown output
