# Trudy 2.0 - Final Requirements Document

## Document Overview

This is the final requirements document for Trudy 2.0, a complete refactoring that transforms Trudy from a single-phase processing system to a modern two-phase atomic workflow system with enhanced markdown formatting, improved CLI interface, and robust state management.

**Status**: Ready for Implementation
**Version**: 2.0
**Date**: 2026-01-04

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Storage Structure](#storage-structure)
4. [Markdown Formats](#markdown-formats)
5. [CLI Interface](#cli-interface)
6. [State Management](#state-management)
7. [Configuration](#configuration)
8. [Processing Features](#processing-features)
9. [Implementation Plan](#implementation-plan)
10. [Documentation Plan](#documentation-plan)
11. [Success Criteria](#success-criteria)

---

## Executive Summary

### What's Changing

Trudy 2.0 introduces a **two-phase architecture** that separates message fetching from processing:

**Current System (v1.x)**:
- Single-phase: Fetch → Process → Save in one operation
- Combined workflows with multiple flags
- Basic markdown format
- Click-based CLI

**New System (v2.0)**:
- **Two-phase**: Phase 1 (Fetch → Staging) + Phase 2 (Staging → Process → Final)
- **Atomic workflows**: Separate commands for discovery, fetching, and processing
- **Enhanced markdown**: Simple staging + Rich processed format with metadata
- **Typer CLI**: Modern interface with better UX and help
- **Single media folder**: Shared across staging and processed areas
- **Auto-discovery only**: Remove manual user configuration

### Key Benefits

1. **Flexibility**: Fetch messages in bulk, process later with different options
2. **Debugging**: Inspect raw messages in staging before processing
3. **Reprocessing**: Easily reprocess with new AI models or settings
4. **Performance**: Parallel processing, batch operations
5. **Reliability**: Atomic operations, better error handling

---

## Architecture Overview

### Two-Phase Processing Model

```
┌─────────────────────────────────────────────────────────────┐
│                        PHASE 1: FETCHING                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Telegram API → MessageFetcher → Staging Writer              │
│                                                               │
│  Actions:                                                     │
│  1. Connect to Telegram Bot API                              │
│  2. Fetch new messages (incremental based on fetch state)    │
│  3. Download media files to shared media/ folder             │
│  4. Convert to simple markdown format                        │
│  5. Save to staging/<username>/YYYY-MM-DD.md                 │
│  6. Update fetch state (last_message_id)                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      PHASE 2: PROCESSING                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Staging Reader → Processors → Enhanced Writer               │
│                                                               │
│  Actions:                                                     │
│  1. Read messages from staging area                          │
│  2. Detect unprocessed messages (checksum-based)             │
│  3. Apply processors:                                        │
│     - Transcription (audio/video → text)                     │
│     - OCR (images → text)                                    │
│     - Summarization (long content → summary)                 │
│     - Link extraction (URLs → metadata)                      │
│     - Auto-tagging (content → tags)                          │
│  4. Generate enhanced markdown with metadata                 │
│  5. Save to processed/<username>/YYYY-MM-DD.md              │
│  6. Update process state (checksums, timestamps)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
trudy/
├── src/
│   ├── cli/                    # NEW: Typer-based CLI
│   │   ├── main.py            # CLI entry point
│   │   ├── discover.py        # User discovery command
│   │   ├── fetch.py           # Fetch command
│   │   ├── process.py         # Process command
│   │   ├── sync.py            # Combined sync command
│   │   ├── status.py          # Status/info commands
│   │   └── utils.py           # Clean and utility commands
│   │
│   ├── core/
│   │   ├── config.py          # Configuration models
│   │   └── state.py           # UPDATED: Unified state management
│   │
│   ├── telegram/
│   │   ├── client.py          # Telegram API wrapper
│   │   ├── fetcher.py         # UPDATED: Fetch-only logic
│   │   └── downloader.py      # Media downloader
│   │
│   ├── markdown/
│   │   ├── staging_writer.py  # NEW: Simple markdown for staging
│   │   ├── staging_reader.py  # NEW: Parse staging files
│   │   ├── processed_writer.py # NEW: Enhanced markdown writer
│   │   └── formatter.py       # Common formatting utilities
│   │
│   ├── processors/            # UPDATED: Work with staging input
│   │   ├── base.py
│   │   ├── text.py
│   │   ├── media.py
│   │   ├── audio_video.py
│   │   ├── link.py            # UPDATED: Extract link metadata
│   │   └── youtube.py
│   │
│   ├── ai/
│   │   ├── transcriber.py     # Audio/video transcription
│   │   ├── summarizer.py      # Content summarization
│   │   ├── ocr.py             # NEW: Image OCR (Tesseract/Cloud)
│   │   └── tagger.py          # NEW: Auto-tagging
│   │
│   └── utils/
│       ├── logger.py
│       ├── checksum.py        # NEW: File checksums
│       └── reporting.py       # NEW: Summary reports
│
├── data/                      # Data directory
│   ├── staging/               # NEW: Raw fetched messages
│   ├── processed/             # NEW: Processed messages
│   ├── media/                 # NEW: Shared media folder
│   └── state.json             # UPDATED: Unified state
│
├── config/
│   └── config.yaml            # UPDATED: New configuration
│
├── logs/
│   ├── trudy.log
│   └── errors.log
│
└── docs/                      # Documentation
    ├── README.md              # User guide
    ├── CLI_REFERENCE.md       # NEW: Complete CLI docs
    ├── MARKDOWN_FORMAT.md     # NEW: Format specifications
    ├── CONFIGURATION.md       # NEW: Config guide
    └── DEVELOPMENT.md         # NEW: Developer guide
```

---

## Storage Structure

### Directory Layout

```
data/
├── staging/
│   ├── alice/
│   │   ├── 2026-01-04.md
│   │   ├── 2026-01-03.md
│   │   └── ...
│   ├── bob/
│   │   └── 2026-01-04.md
│   └── ...
│
├── processed/
│   ├── alice/
│   │   ├── 2026-01-04.md
│   │   ├── 2026-01-03.md
│   │   └── ...
│   ├── bob/
│   │   └── 2026-01-04.md
│   └── ...
│
├── media/                      # Shared media folder
│   ├── alice/
│   │   ├── 2026-01-04_14-35-23_image.jpg
│   │   ├── 2026-01-04_14-40-15_video.mp4
│   │   ├── 2026-01-04_14-40-15_video_transcript.txt
│   │   ├── 2026-01-04_14-45-30_audio.ogg
│   │   ├── 2026-01-04_14-45-30_audio_transcript.txt
│   │   └── ...
│   ├── bob/
│   │   └── ...
│   └── ...
│
└── state.json                  # Single unified state file
```

### Key Design Decisions

1. **Single Media Folder**: All media files (original + transcripts) stored in `data/media/<username>/`
2. **Separate Staging/Processed**: Markdown files kept separate for clarity
3. **User-Based Organization**: Each user has their own subdirectories
4. **Date-Based Files**: One markdown file per user per day
5. **Relative References**: Markdown files reference media using relative paths

### Media File Naming Convention

```
Format: YYYY-MM-DD_HH-MM-SS_<type>.<ext>

Examples:
- 2026-01-04_14-35-23_image.jpg
- 2026-01-04_14-40-15_meeting_video.mp4
- 2026-01-04_14-40-15_meeting_video_transcript.txt
- 2026-01-04_14-45-30_voice.ogg
- 2026-01-04_14-45-30_voice_transcript.txt
```

### Staging Retention Policy

**Configurable retention** with these options:
- `keep_all`: Never delete staging files (default for debugging)
- `keep_days: N`: Keep staging files for N days after processing
- `delete_after_process`: Delete immediately after successful processing

Configured in `config.yaml`:
```yaml
storage:
  staging_retention:
    policy: "keep_days"  # keep_all | keep_days | delete_after_process
    days: 7              # Used when policy is "keep_days"
```

---

## Markdown Formats

### Staging Format (Simple & Raw)

**Purpose**: Capture raw messages as-is from Telegram with minimal processing.

**Design Principles**:
- Verbatim text in headers for easy scanning
- Minimal structure, no metadata
- Human-readable timestamps
- Direct media links

**Format Specification**:

```markdown
## 14:30 - Hello, this is a test message

---

## 14:35 - [Image]

![](../media/alice/2026-01-04_14-35-23_image.jpg)

Caption: My screenshot

---

## 14:40 - [Video]

[Video](../media/alice/2026-01-04_14-40-15_video.mp4)

Caption: Important meeting recording

---

## 14:45 - [Voice Message]

[Audio](../media/alice/2026-01-04_14-45-30_voice.ogg)

---

## 14:50 - Check out this article: https://example.com/article

---

## 15:00 - [Document]

[Q4_Report.pdf](../media/alice/2026-01-04_15-00-12_document.pdf)

---

## 15:05 - Here's a great video

https://www.youtube.com/watch?v=dQw4w9WgXcQ

---
```

**Header Format Rules**:
- **Text messages**: `## HH:MM - <first 50 chars of text>`
- **Media with caption**: `## HH:MM - [Media Type]` (full caption below)
- **Media without caption**: `## HH:MM - [Media Type]`
- **Links**: `## HH:MM - <first 50 chars including URL>`

### Processed Format (Enhanced with Metadata)

**Purpose**: Rich, searchable, AI-enhanced messages with metadata for knowledge management.

**Design Principles**:
- YAML-style indented metadata blocks
- Obsidian-compatible wikilinks
- Comprehensive tagging
- Transcripts and summaries included
- Link metadata extracted

**Format Specification**:

```markdown
## 14:30 - Hello, this is a test message
type: text
content: |-
  Hello, this is a test message with a link: https://example.com/article
links:
  - url: https://example.com/article
    title: "Example Article Title"
    description: "A comprehensive guide to example articles..."
tags:
  - #communication
  - #example

---

## 14:35 - [Image]
type: image
file: ![[2026-01-04_14-35-23_image.jpg]]
caption: My screenshot
ocr_text: |-
  Error: Connection timeout
  Please check your network settings
tags:
  - #screenshot
  - #error
  - #troubleshooting

---

## 14:40 - [Video]
type: video
file: ![[2026-01-04_14-40-15_video.mp4]]
duration: 15:32
caption: Important meeting recording
summary: |-
  - Discussed Q1 roadmap priorities
  - Reviewed customer feedback from December
  - Action items assigned for next sprint
  - Budget allocation for new features
transcript: ![[2026-01-04_14-40-15_video_transcript.txt]]
tags:
  - #meeting
  - #planning
  - #video

---

## 14:45 - [Voice Message]
type: voice
file: ![[2026-01-04_14-45-30_voice.ogg]]
duration: 00:45
summary: Reminder to review the PR before end of day
transcript: ![[2026-01-04_14-45-30_voice_transcript.txt]]
tags:
  - #reminder
  - #voice

---

## 14:50 - Check out this article
type: text
content: |-
  Check out this article: https://example.com/article
links:
  - url: https://example.com/article
    title: "Building Scalable Systems"
    description: "Learn how to design systems that scale..."
tags:
  - #article
  - #learning
  - #architecture

---

## 15:00 - [Document]
type: document
file: ![[2026-01-04_15-00-12_document.pdf]]
filename: Q4_Financial_Report.pdf
size: 2.4 MB
tags:
  - #document
  - #finance
  - #report

---

## 15:05 - Here's a great video
type: youtube
url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
title: "Rick Astley - Never Gonna Give You Up"
channel: "Rick Astley"
duration: 03:33
summary: |-
  - Classic 80s pop music video
  - Iconic dance moves and fashion
  - Cultural phenomenon and internet meme
transcript: ![[2026-01-04_15-05-00_youtube_transcript.txt]]
tags:
  - #music
  - #youtube
  - #80s

---

## 15:10 - Re: Can you review this?
type: text
content: |-
  Yes, I'll review it by EOD tomorrow
reply_to:
  message_id: 1234
  timestamp: "2026-01-04T14:00:00"
  preview: "Can you review this design document?"
tags:
  - #reply
  - #review

---

## 15:15 - [Forwarded Message]
type: text
content: |-
  Important announcement: Server maintenance scheduled for tonight
forwarded_from:
  user: "IT Team"
  chat_id: 987654321
  original_date: "2026-01-04T12:00:00"
tags:
  - #forwarded
  - #announcement
  - #maintenance

---
```

### Metadata Field Reference

| Field | Type | Description | Applies To |
|-------|------|-------------|------------|
| `type` | string | Message type: text, image, photo, video, video_note, audio, voice, youtube, document | All |
| `content` | string | Text content (verbatim) | text |
| `file` | wikilink | Obsidian wikilink to media file | image, video, audio, voice, document |
| `url` | string | Direct URL | youtube |
| `caption` | string | Media caption from Telegram | image, video, audio, document |
| `duration` | string | Media duration (MM:SS or HH:MM:SS) | video, audio, voice, youtube |
| `summary` | string | AI-generated summary (multi-line) | video, audio, voice, youtube |
| `transcript` | wikilink | Link to transcript file | video, audio, voice, youtube |
| `ocr_text` | string | Extracted text from images | image, photo |
| `links` | array | Extracted link metadata | text (if contains URLs) |
| `links[].url` | string | URL | text |
| `links[].title` | string | Page title | text |
| `links[].description` | string | Meta description | text |
| `tags` | array | Auto-generated tags | All |
| `filename` | string | Original filename | document |
| `size` | string | File size (human-readable) | document |
| `title` | string | Video title | youtube |
| `channel` | string | Channel name | youtube |
| `reply_to` | object | Reply context | text (if reply) |
| `reply_to.message_id` | integer | Original message ID | text (if reply) |
| `reply_to.timestamp` | string | Original timestamp (ISO 8601) | text (if reply) |
| `reply_to.preview` | string | First 100 chars of original message | text (if reply) |
| `forwarded_from` | object | Forward context | All (if forwarded) |
| `forwarded_from.user` | string | Original sender | All (if forwarded) |
| `forwarded_from.chat_id` | integer | Original chat ID | All (if forwarded) |
| `forwarded_from.original_date` | string | Original timestamp (ISO 8601) | All (if forwarded) |
| `edited_at` | string | Last edit timestamp (ISO 8601) | All (if edited) |

### Wikilink Format

**Obsidian-style wikilinks** for all media references:
- Images: `![[filename.jpg]]` (embedded image)
- Videos: `![[filename.mp4]]` (embedded video)
- Audio: `![[filename.ogg]]` (embedded audio)
- Documents: `![[filename.pdf]]` (link to document)
- Transcripts: `![[filename_transcript.txt]]` (link to transcript)

**Path Resolution**:
- Markdown files reference media using `![[filename]]` format
- Obsidian resolves these automatically if media folder is in vault
- Relative paths: `../media/<username>/filename.ext` (for non-Obsidian viewers)

---

## CLI Interface

### CLI Framework: Typer

**Benefits**:
- Type-safe arguments with validation
- Automatic help generation
- Rich terminal output
- Subcommands support
- Better error messages

### Command Structure (Flat)

```bash
trudy discover       # Discover users
trudy fetch          # Fetch messages to staging
trudy process        # Process staging to final
trudy sync           # Fetch + Process (convenience)
trudy status         # Show sync status
trudy info           # Show system info
trudy clean          # Clean data directories
```

### Complete CLI Reference

#### 1. User Discovery

```bash
trudy discover [OPTIONS]
```

**Purpose**: Scan Telegram messages and discover users who have messaged the bot.

**Options**:
```
--full              Scan all historical messages (default: incremental)
--refresh           Re-scan and update user list
--format [table|json]  Output format (default: table)
-v, --verbose       Enable verbose logging
-h, --help          Show help
```

**Output**: Table or JSON list of discovered users with metadata.

**Examples**:
```bash
# Discover new users (incremental)
trudy discover

# Full re-scan of all messages
trudy discover --full

# Output as JSON
trudy discover --format json

# Verbose mode for debugging
trudy discover -v
```

**Sample Output (table)**:
```
┌──────────┬─────────────┬────────────────┬────────────────────┐
│ Username │ Chat ID     │ First Seen     │ Last Seen          │
├──────────┼─────────────┼────────────────┼────────────────────┤
│ alice    │ 123456789   │ 2026-01-01     │ 2026-01-04 15:30   │
│ bob      │ 987654321   │ 2026-01-03     │ 2026-01-04 14:20   │
└──────────┴─────────────┴────────────────┴────────────────────┘
```

---

#### 2. Message Fetching

```bash
trudy fetch [OPTIONS] [USERS...]
```

**Purpose**: Fetch messages from Telegram and save to staging area.

**Options**:
```
--all               Fetch for all discovered users (default)
--user <username>   Fetch for specific user(s), repeatable
--full              Full sync (all history), default: incremental
--limit <n>         Limit number of messages to fetch per user
--dry-run           Preview what would be fetched without writing
-v, --verbose       Enable verbose logging
-h, --help          Show help
```

**Positional Arguments**:
```
USERS               Optional list of usernames to fetch (alternative to --user)
```

**Output**: Progress bar + summary report.

**Examples**:
```bash
# Fetch new messages for all users (incremental)
trudy fetch

# Fetch for specific users
trudy fetch alice bob
trudy fetch --user alice --user bob

# Full sync for all users (all history)
trudy fetch --full

# Fetch with limit
trudy fetch --user alice --limit 100

# Dry run (preview only)
trudy fetch --dry-run

# Verbose mode
trudy fetch -v
```

**Sample Output**:
```
Fetching messages...

alice: ████████████████████ 50/50 messages
bob:   ████████████████████ 23/23 messages

✓ Fetch completed

Summary:
  Users processed: 2
  Messages fetched: 73
  Media downloaded: 15
  Errors: 0
  Time elapsed: 12.3s
```

---

#### 3. Message Processing

```bash
trudy process [OPTIONS] [USERS...]
```

**Purpose**: Process staged messages and generate enriched markdown.

**Options**:
```
--all                 Process all users (default)
--user <username>     Process specific user(s), repeatable
--date <YYYY-MM-DD>   Process specific date only
--skip-transcription  Skip audio/video transcription
--skip-ocr            Skip image OCR
--skip-summarization  Skip AI summarization
--skip-tags           Skip automatic tag generation
--skip-links          Skip link metadata extraction
--reprocess           Force reprocess already processed messages
--workers <n>         Number of parallel workers (default: 3)
--dry-run             Preview what would be processed
-v, --verbose         Enable verbose logging
-h, --help            Show help
```

**Positional Arguments**:
```
USERS                 Optional list of usernames to process
```

**Output**: Progress bar + summary report.

**Examples**:
```bash
# Process all pending messages (incremental)
trudy process

# Process specific users
trudy process alice bob
trudy process --user alice

# Process specific date
trudy process --date 2026-01-04

# Skip expensive operations
trudy process --skip-transcription --skip-summarization

# Reprocess with new AI models
trudy process --all --reprocess

# Fast processing (skip all AI)
trudy process --skip-transcription --skip-ocr --skip-summarization

# Parallel processing with more workers
trudy process --workers 5

# Dry run
trudy process --dry-run -v
```

**Sample Output**:
```
Processing messages...

alice (2026-01-04.md): ████████████████████ 25/25 messages
  - Transcribed: 3 videos, 2 voice messages
  - OCR: 5 images
  - Summarized: 8 items
  - Tags generated: 25 messages

bob (2026-01-04.md): ████████████████████ 10/10 messages
  - Transcribed: 1 video
  - Tags generated: 10 messages

✓ Processing completed

Summary:
  Users processed: 2
  Messages processed: 35
  Transcriptions: 6
  OCR performed: 5
  Summaries generated: 8
  Tags generated: 35
  Links extracted: 4
  Errors: 0
  Time elapsed: 2m 15s
```

---

#### 4. Combined Workflow (Sync)

```bash
trudy sync [OPTIONS] [USERS...]
```

**Purpose**: Convenience command that runs `fetch` then `process`.

**Options**: Accepts combined options from both fetch and process commands.
```
--all                 Sync all users (default)
--user <username>     Sync specific user(s), repeatable
--full                Full sync (all history)
--limit <n>           Limit messages to fetch
--skip-transcription  Skip transcription during processing
--skip-ocr            Skip OCR during processing
--skip-summarization  Skip summarization during processing
--skip-tags           Skip tag generation
--workers <n>         Number of processing workers
--dry-run             Preview without writing
-v, --verbose         Verbose logging
-h, --help            Show help
```

**Examples**:
```bash
# Daily sync (incremental)
trudy sync

# Full sync for specific user
trudy sync --user alice --full

# Quick sync (skip AI features)
trudy sync --skip-summarization --skip-transcription

# Sync with custom workers
trudy sync --workers 5
```

---

#### 5. Status & Information

```bash
trudy status [OPTIONS]
```

**Purpose**: Show sync status, message counts, last sync times.

**Options**:
```
--user <username>     Show status for specific user
--format [table|json] Output format (default: table)
-h, --help            Show help
```

**Examples**:
```bash
# Show status for all users
trudy status

# Show status for specific user
trudy status --user alice

# JSON output
trudy status --format json
```

**Sample Output**:
```
┌──────────┬──────────┬────────────┬──────────────┬─────────────────────┬─────────────────────┐
│ User     │ Fetched  │ Processed  │ Pending      │ Last Fetch          │ Last Process        │
├──────────┼──────────┼────────────┼──────────────┼─────────────────────┼─────────────────────┤
│ alice    │ 523      │ 520        │ 3            │ 2026-01-04 15:30    │ 2026-01-04 15:25    │
│ bob      │ 187      │ 187        │ 0            │ 2026-01-04 14:20    │ 2026-01-04 14:22    │
└──────────┴──────────┴────────────┴──────────────┴─────────────────────┴─────────────────────┘

Total: 710 fetched, 707 processed, 3 pending
```

---

```bash
trudy info
```

**Purpose**: Show configuration, model status, system info.

**Output**: System configuration and health check.

**Example Output**:
```
Trudy 2.0 - Personal Knowledge Management Bot

Configuration:
  Data directory: /Users/user/data
  Timezone: America/New_York

Models:
  Transcription: Ollama Whisper (✓ available)
  Summarization: Ollama llama2 (✓ available)
  OCR: Tesseract (✓ installed)

Statistics:
  Total users: 2
  Total messages: 710 fetched, 707 processed
  Media files: 142
  Transcriptions: 45
  Summaries: 120

System:
  Python: 3.11.4
  Platform: macOS 14.0
```

---

#### 6. Utilities

```bash
trudy clean [OPTIONS]
```

**Purpose**: Clean staging or processed areas.

**Options**:
```
--staging             Clean staging area
--processed           Clean processed area (dangerous!)
--media               Clean media folder (dangerous!)
--user <username>     Clean specific user's data
--before <YYYY-MM-DD> Clean data before specific date
--dry-run             Preview what would be deleted
-h, --help            Show help
```

**Examples**:
```bash
# Clean old staging files (based on retention policy)
trudy clean --staging

# Clean staging for specific user
trudy clean --staging --user alice

# Clean staging files before specific date
trudy clean --staging --before 2025-12-01

# Dry run to preview
trudy clean --staging --dry-run

# DANGEROUS: Clean all processed files (requires confirmation)
trudy clean --processed
```

---

### Global Options

All commands support these global options:
```
-v, --verbose         Increase logging verbosity (DEBUG level)
--quiet               Suppress non-error output
--config <path>       Use custom config file (default: config/config.yaml)
--help                Show help message
--version             Show version information
```

---

## State Management

### Single Unified State File

**File**: `data/state.json`

**Structure**:
```json
{
  "version": "2.0",
  "users": {
    "alice": {
      "chat_id": 123456789,
      "phone": "+1234567890",
      "first_seen": "2026-01-01T10:00:00-05:00",
      "last_seen": "2026-01-04T15:30:00-05:00",

      "fetch_state": {
        "last_message_id": 1234,
        "last_fetch_time": "2026-01-04T15:30:00-05:00",
        "total_messages_fetched": 523
      },

      "process_state": {
        "last_processed_date": "2026-01-04",
        "last_process_time": "2026-01-04T15:25:00-05:00",
        "total_messages_processed": 520,
        "file_checksums": {
          "staging/alice/2026-01-04.md": "a1b2c3d4e5f6",
          "staging/alice/2026-01-03.md": "f6e5d4c3b2a1"
        },
        "pending_files": [
          "staging/alice/2026-01-04.md"
        ]
      }
    },
    "bob": {
      "chat_id": 987654321,
      "phone": "+9876543210",
      "first_seen": "2026-01-03T08:00:00-05:00",
      "last_seen": "2026-01-04T14:20:00-05:00",

      "fetch_state": {
        "last_message_id": 567,
        "last_fetch_time": "2026-01-04T14:20:00-05:00",
        "total_messages_fetched": 187
      },

      "process_state": {
        "last_processed_date": "2026-01-04",
        "last_process_time": "2026-01-04T14:22:00-05:00",
        "total_messages_processed": 187,
        "file_checksums": {
          "staging/bob/2026-01-04.md": "9876543210ab"
        },
        "pending_files": []
      }
    }
  },

  "statistics": {
    "total_users": 2,
    "total_messages_fetched": 710,
    "total_messages_processed": 707,
    "total_media": 142,
    "total_transcriptions": 45,
    "total_summaries": 120,
    "total_ocr": 32,
    "total_tags": 707,
    "total_links_extracted": 89
  }
}
```

### State Fields Explanation

**User-Level Fields**:
- `chat_id`: Telegram chat ID
- `phone`: Phone number (if available)
- `first_seen`: First message timestamp (ISO 8601 with timezone)
- `last_seen`: Last message timestamp

**Fetch State** (tracks fetching progress):
- `last_message_id`: Last fetched Telegram message ID (for incremental fetching)
- `last_fetch_time`: Timestamp of last fetch operation
- `total_messages_fetched`: Cumulative count

**Process State** (tracks processing progress):
- `last_processed_date`: Last date that was fully processed
- `last_process_time`: Timestamp of last process operation
- `total_messages_processed`: Cumulative count
- `file_checksums`: SHA-256 checksums of staging files (to detect changes)
- `pending_files`: List of staging files not yet processed

**Global Statistics**:
- Cumulative counts across all users
- Used for reporting and analytics

### State Update Logic

**Fetch Operation**:
1. Read current `fetch_state.last_message_id`
2. Fetch messages with `message_id > last_message_id`
3. Update `fetch_state.last_message_id` to highest fetched ID
4. Update `fetch_state.total_messages_fetched`
5. Add staging file to `process_state.pending_files` if new

**Process Operation**:
1. Read staging files from `pending_files`
2. Calculate checksum of staging file
3. Compare with `file_checksums[file]`
4. If different or `--reprocess` flag:
   - Process the file
   - Update checksum
   - Remove from `pending_files` if successful
5. Update `process_state.total_messages_processed`

**Checksum-Based Reprocessing**:
- Only reprocess if staging file has changed (default)
- `--reprocess` flag forces processing regardless of checksum
- Enables efficient reprocessing with new AI models or settings

### State Atomicity

**File Locking**:
- Use file locking to prevent concurrent state.json writes
- Atomic writes (write to temp file, then rename)

**Error Recovery**:
- Keep backup of state.json before updates
- Rollback on errors
- Validate state.json structure on load

---

## Configuration

### Configuration File Structure

**File**: `config/config.yaml`

```yaml
# Telegram Bot Configuration
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # From environment variable
  api_url: "https://api.telegram.org"
  timeout: 30
  retry_attempts: 3
  retry_delay: 5  # seconds

# Storage Configuration
storage:
  base_dir: "./data"
  staging_dir: "staging"
  processed_dir: "processed"
  media_dir: "media"  # Shared media folder

  # Staging retention policy
  staging_retention:
    policy: "keep_days"  # keep_all | keep_days | delete_after_process
    days: 7              # Used when policy is "keep_days"

# Transcription Configuration
transcription:
  enabled: true
  provider: "ollama"  # ollama | remote_api

  ollama:
    base_url: "http://localhost:11434"
    model: "whisper"
    timeout: 300

  # YouTube-specific settings
  youtube_prefer_transcript: true  # Use YouTube API for transcripts when available

# Summarization Configuration
summarization:
  enabled: true
  provider: "ollama"  # ollama | claude

  ollama:
    base_url: "http://localhost:11434"
    model: "llama2"
    temperature: 0.7
    max_tokens: 500

  claude:
    cli_path: "claude"
    model: "claude-sonnet-4-5"
    max_tokens: 1000

  # Prompts for different content types
  prompts:
    video_summary: "Summarize the key points from this video transcript in 3-5 bullet points."
    audio_summary: "Summarize the main topics discussed in this audio recording in 2-4 bullet points."
    article_summary: "Provide a concise summary of this article in 2-3 paragraphs."
    youtube_summary: "Summarize this YouTube video, highlighting key takeaways in bullet points."

# OCR Configuration
ocr:
  enabled: true
  provider: "tesseract"  # tesseract | cloud

  tesseract:
    languages: ["eng"]  # OCR languages
    config: "--psm 3"   # Page segmentation mode

  cloud:
    provider: "google_vision"  # google_vision | azure | aws
    api_key: "${OCR_API_KEY}"
    # Add provider-specific config here

# Link Extraction Configuration
links:
  enabled: true
  timeout: 10  # seconds
  user_agent: "Trudy/2.0 (Personal Knowledge Bot)"
  extract:
    title: true
    description: true
    opengraph: false  # Disabled per user preference
    favicon: false    # Disabled per user preference

# Auto-Tagging Configuration
tagging:
  enabled: true

  # Rule-based tags (fast, deterministic)
  rules:
    - pattern: "screenshot"
      tag: "#screenshot"
    - pattern: "meeting"
      tag: "#meeting"
    - pattern: "reminder"
      tag: "#reminder"
    - pattern: "todo|task"
      tag: "#task"
    - pattern: "\\.pdf$"
      tag: "#document"
    - pattern: "youtube\\.com|youtu\\.be"
      tag: "#youtube"

  # AI-based tagging (optional, slower)
  ai_tagging:
    enabled: false  # Disabled by default
    provider: "ollama"
    model: "llama2"
    max_tags: 5
    prompt: "Generate 3-5 relevant hashtags for this message. Return only hashtags separated by commas."

# Processing Configuration
processing:
  max_workers: 3          # Parallel processing workers
  skip_errors: true       # Continue on errors
  retry_failed: true      # Retry failed messages
  max_retries: 3

  # Progress reporting
  show_progress: true
  report_interval: 10  # Update progress every N messages

# Markdown Configuration
markdown:
  timezone: "America/New_York"  # Local timezone for timestamps
  timestamp_format: "HH:mm"     # 24-hour format
  date_format: "YYYY-MM-DD"

  # Wikilink style
  wikilink_style: "obsidian"  # obsidian | markdown

  # Include additional metadata
  include_message_id: false   # Include Telegram message ID in markdown
  include_edit_history: true  # Track message edits

# Logging Configuration
logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

  # Log files
  file: "./logs/trudy.log"
  error_file: "./logs/errors.log"

  # Log rotation
  max_bytes: 10485760  # 10 MB
  backup_count: 5

  # Console output
  console_level: "INFO"
  use_colors: true
```

### Environment Variables

**Required**:
- `TELEGRAM_BOT_TOKEN`: Telegram bot token from @BotFather

**Optional**:
- `OCR_API_KEY`: Cloud OCR API key (if using cloud provider)
- `GOOGLE_VISION_API_KEY`: Google Cloud Vision API key
- `AZURE_VISION_KEY`: Azure Computer Vision key
- `AWS_ACCESS_KEY_ID`: AWS Rekognition credentials
- `AWS_SECRET_ACCESS_KEY`: AWS Rekognition credentials

**Example `.env` file**:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
OCR_API_KEY=your_cloud_ocr_key_here
```

---

## Processing Features

### 1. Transcription

**Supported Media**:
- Audio files (mp3, ogg, m4a, wav)
- Voice messages (ogg)
- Video files (mp4, mov, avi)
- Video notes (Telegram round videos)

**Providers**:
- **Ollama Whisper** (default): Local, free, good quality
- **Remote API**: OpenAI Whisper API (better quality, costs money)

**Output**:
- Transcript saved as `.txt` file in media folder
- Referenced in processed markdown via wikilink
- Summary generated from transcript (if summarization enabled)

**Configuration**:
```yaml
transcription:
  enabled: true
  provider: "ollama"
  ollama:
    model: "whisper"
    timeout: 300
```

---

### 2. OCR (Optical Character Recognition)

**Supported Media**:
- Images (jpg, png, gif)
- Photos

**Providers**:
- **Tesseract** (default): Local, free, good for printed text
- **Cloud OCR**: Google Vision, Azure, AWS (better quality, costs money)

**Output**:
- Extracted text embedded in processed markdown as `ocr_text` field
- Multi-language support
- Structured text extraction

**Configuration**:
```yaml
ocr:
  enabled: true
  provider: "tesseract"
  tesseract:
    languages: ["eng"]
    config: "--psm 3"
```

---

### 3. Summarization

**Supported Content**:
- Video transcripts
- Audio transcripts
- Long text messages
- Article content
- YouTube video transcripts

**Providers**:
- **Ollama** (default): Local models (llama2, mistral, etc.)
- **Claude**: Claude Code CLI for higher quality summaries

**Output**:
- Bullet-point summaries embedded in processed markdown
- Customizable prompts per content type

**Configuration**:
```yaml
summarization:
  enabled: true
  provider: "ollama"
  ollama:
    model: "llama2"
    temperature: 0.7
  prompts:
    video_summary: "Summarize the key points..."
```

---

### 4. Link Extraction

**Supported Links**:
- HTTP/HTTPS URLs in text messages
- Article links
- General web pages

**Extracted Metadata**:
- Page title (from `<title>` tag)
- Meta description (from `<meta name="description">`)

**Output**:
- `links` array in processed markdown with URL, title, description

**Configuration**:
```yaml
links:
  enabled: true
  timeout: 10
  extract:
    title: true
    description: true
```

**Example Output**:
```yaml
links:
  - url: https://example.com/article
    title: "How to Build Scalable Systems"
    description: "Learn the principles of designing systems that scale..."
```

---

### 5. Auto-Tagging

**Tagging Strategies**:

**Rule-Based** (fast, deterministic):
- Pattern matching on content
- File type detection
- Keyword extraction
- Always enabled

**AI-Based** (optional, slower):
- Use LLM to generate contextual tags
- Analyze content semantically
- Disabled by default

**Tag Format**:
- Hashtag style: `#tag`
- Lowercase, underscores for spaces
- Examples: `#screenshot`, `#meeting`, `#task`

**Configuration**:
```yaml
tagging:
  enabled: true
  rules:
    - pattern: "screenshot"
      tag: "#screenshot"
    - pattern: "meeting"
      tag: "#meeting"
  ai_tagging:
    enabled: false
    max_tags: 5
```

**Built-in Rules**:
- `screenshot` → `#screenshot`
- `meeting` → `#meeting`
- `reminder|remind` → `#reminder`
- `todo|task` → `#task`
- `\.pdf$` → `#document`
- `youtube\.com|youtu\.be` → `#youtube`
- `image|photo` → `#image`
- `video` → `#video`
- `audio|voice` → `#audio`

---

### 6. YouTube Handling

**Detection**:
- URLs matching `youtube.com/watch?v=` or `youtu.be/`

**Processing**:
1. Extract video ID
2. Fetch metadata (title, channel, duration)
3. Attempt to fetch transcript via YouTube API
4. If transcript unavailable, download and transcribe (if enabled)
5. Generate summary from transcript

**Output**:
- Dedicated YouTube entry in processed markdown
- Transcript saved as `.txt` file
- Summary in bullet points

**Configuration**:
```yaml
transcription:
  youtube_prefer_transcript: true  # Prefer API transcript over download
```

---

### 7. Reply & Forward Context

**Reply Tracking**:
- Detect when message is a reply
- Include `reply_to` metadata with:
  - Original message ID
  - Original timestamp
  - Preview (first 100 chars)

**Forward Tracking**:
- Detect when message is forwarded
- Include `forwarded_from` metadata with:
  - Original sender
  - Original chat ID
  - Original timestamp

**Output**:
```yaml
## 15:10 - Re: Can you review this?
type: text
content: |-
  Yes, I'll review it by EOD tomorrow
reply_to:
  message_id: 1234
  timestamp: "2026-01-04T14:00:00-05:00"
  preview: "Can you review this design document?"
```

---

### 8. Edit Tracking

**Detection**:
- Telegram messages can be edited
- Track edit history

**Output**:
```yaml
## 14:30 - Updated meeting time
type: text
content: |-
  Meeting rescheduled to 3 PM (updated)
edited_at: "2026-01-04T14:35:00-05:00"
```

---

## Implementation Plan

### Phase 0: Preparation (Day 1)

**Goals**: Set up new project structure, update dependencies

**Tasks**:
1. Remove old data structure (no backward compatibility needed)
2. Update `pyproject.toml`:
   - Replace `click` with `typer[all]`
   - Add `PyYAML`, `rich`, `aiofiles`
   - Add `pytesseract` for OCR
   - Add `beautifulsoup4` for link extraction
3. Create new directory structure:
   ```
   data/staging/
   data/processed/
   data/media/
   ```
4. Create placeholder state.json
5. Update config.yaml with new structure

**Deliverables**:
- ✅ Clean project structure
- ✅ Dependencies updated
- ✅ Directory structure created
- ✅ Configuration updated

---

### Phase 1: Core Infrastructure (Days 2-3)

**Goals**: Build state management, storage utilities, checksum handling

**Tasks**:

**Day 2: State Management**
1. Update `src/core/state.py`:
   - Unified state structure with `fetch_state` and `process_state`
   - Checksum storage and validation
   - Pending files tracking
   - File locking for atomic updates
   - Backup and rollback mechanisms
2. Add `src/utils/checksum.py`:
   - SHA-256 checksum calculation
   - File comparison utilities
3. Write unit tests for state management

**Day 3: Storage & Configuration**
1. Update `src/core/config.py`:
   - New configuration models for all features
   - Link extraction config
   - OCR config
   - Tagging config
   - Staging retention config
2. Create `src/utils/storage.py`:
   - Directory creation utilities
   - Path resolution (staging, processed, media)
   - Media file naming
3. Write unit tests for config loading

**Deliverables**:
- ✅ Unified state management
- ✅ Checksum utilities
- ✅ Updated configuration models
- ✅ Storage utilities
- ✅ Unit tests passing

---

### Phase 2: Fetching Layer (Days 4-5)

**Goals**: Implement Phase 1 (Fetch to Staging)

**Tasks**:

**Day 4: Staging Writer**
1. Create `src/markdown/staging_writer.py`:
   - Simple markdown format
   - Verbatim text in headers
   - Media links (relative paths to shared media folder)
   - Daily file append logic
2. Create `src/markdown/formatter.py`:
   - Common formatting utilities (timestamps, sanitization)
   - Timezone handling
3. Write unit tests for staging writer

**Day 5: Refactor Fetcher**
1. Update `src/telegram/fetcher.py`:
   - Remove processing logic (fetch only)
   - Save to staging using StagingWriter
   - Update fetch_state only
   - Add to pending_files in process_state
2. Update `src/telegram/downloader.py`:
   - Download to shared `media/<username>/` folder
   - File naming with timestamps
3. Write integration tests for fetching

**Deliverables**:
- ✅ Staging markdown writer
- ✅ Refactored fetcher (no processing)
- ✅ Media downloader updated
- ✅ Tests passing

---

### Phase 3: Processing Layer (Days 6-8)

**Goals**: Implement Phase 2 (Staging to Processed)

**Tasks**:

**Day 6: Staging Reader & Processed Writer**
1. Create `src/markdown/staging_reader.py`:
   - Parse staging markdown files
   - Extract messages with metadata
   - Return list of Message objects
2. Create `src/markdown/processed_writer.py`:
   - Enhanced markdown format with YAML blocks
   - Wikilinks for media
   - Metadata formatting
   - Daily file append logic
3. Write unit tests for both

**Day 7: Refactor Processors**
1. Update all processors in `src/processors/`:
   - Work with staging input
   - Return metadata for processed format
   - Update `TextProcessor`, `MediaProcessor`, `AudioVideoProcessor`
2. Create `src/processors/link.py`:
   - Link detection in text
   - Metadata extraction (title, description)
   - Error handling for failed fetches
3. Write unit tests for processors

**Day 8: Processing Orchestration**
1. Create `src/core/processor.py`:
   - Orchestrate processing pipeline
   - Read from staging
   - Apply processors
   - Write to processed
   - Update process_state with checksums
   - Handle errors and retries
2. Implement parallel processing with workers
3. Write integration tests for processing pipeline

**Deliverables**:
- ✅ Staging reader
- ✅ Processed markdown writer
- ✅ Refactored processors
- ✅ Link extraction processor
- ✅ Processing orchestration
- ✅ Tests passing

---

### Phase 4: AI Features (Days 9-10)

**Goals**: Implement OCR, enhanced tagging, link extraction

**Tasks**:

**Day 9: OCR & Link Extraction**
1. Create `src/ai/ocr.py`:
   - Tesseract integration
   - Cloud OCR providers (Google Vision, Azure, AWS)
   - Language support
   - Error handling
2. Update `src/processors/link.py`:
   - HTTP requests with timeouts
   - HTML parsing (BeautifulSoup)
   - Extract title from `<title>` tag
   - Extract description from `<meta name="description">`
3. Write unit tests (mock HTTP requests)

**Day 10: Auto-Tagging**
1. Create `src/ai/tagger.py`:
   - Rule-based tagging engine
   - Pattern matching
   - AI-based tagging (optional)
   - Tag formatting and deduplication
2. Integrate tagger into processing pipeline
3. Write unit tests for tagging rules

**Deliverables**:
- ✅ OCR implementation (Tesseract + Cloud)
- ✅ Link metadata extraction
- ✅ Auto-tagging (rules + AI)
- ✅ Tests passing

---

### Phase 5: CLI Commands (Days 11-12)

**Goals**: Implement all Typer-based CLI commands

**Tasks**:

**Day 11: Core Commands**
1. Create `src/cli/main.py`:
   - Typer app initialization
   - Global options (--verbose, --config)
   - Version command
2. Create `src/cli/discover.py`:
   - User discovery logic
   - Table and JSON output
3. Create `src/cli/fetch.py`:
   - Fetch command implementation
   - Progress bar (Rich)
   - Summary reporting
4. Create `src/cli/process.py`:
   - Process command implementation
   - Worker pool management
   - Progress bar and reporting

**Day 12: Convenience & Utility Commands**
1. Create `src/cli/sync.py`:
   - Combined fetch + process
   - Option passing
2. Create `src/cli/status.py`:
   - Status command (read state.json)
   - Info command (system info)
   - Table and JSON output
3. Create `src/cli/utils.py`:
   - Clean command
   - Dry-run support
   - Confirmation prompts
4. Create `src/utils/reporting.py`:
   - Summary report generation
   - Statistics formatting

**Deliverables**:
- ✅ All CLI commands implemented
- ✅ Rich output formatting
- ✅ Progress bars and reporting
- ✅ Help documentation auto-generated
- ✅ Manual testing of all commands

---

### Phase 6: Advanced Features (Days 13-14)

**Goals**: Reply/forward context, edit tracking, conversation threading

**Tasks**:

**Day 13: Message Context**
1. Update `src/telegram/fetcher.py`:
   - Extract reply metadata
   - Extract forward metadata
   - Track message edits
2. Update `src/markdown/processed_writer.py`:
   - Include reply_to metadata
   - Include forwarded_from metadata
   - Include edited_at timestamp
3. Write unit tests

**Day 14: Conversation Threading**
1. Create `src/utils/threading.py`:
   - Detect related messages
   - Group by reply chains
   - Add conversation context to metadata
2. Integrate into processing pipeline
3. Write unit tests

**Deliverables**:
- ✅ Reply context tracking
- ✅ Forward context tracking
- ✅ Edit tracking
- ✅ Conversation threading (basic)
- ✅ Tests passing

---

### Phase 7: Testing & Polish (Days 15-16)

**Goals**: Comprehensive testing, bug fixes, performance optimization

**Tasks**:

**Day 15: Testing**
1. Write integration tests:
   - End-to-end workflow (discover → fetch → process)
   - Error scenarios
   - Edge cases (empty messages, large files, etc.)
2. Write system tests:
   - Test with real Telegram bot (small dataset)
   - Validate markdown output
   - Check media downloads
3. Performance testing:
   - Benchmark parallel processing
   - Optimize checksum calculations
   - Profile slow operations

**Day 16: Bug Fixes & Polish**
1. Fix bugs discovered during testing
2. Improve error messages
3. Add validation and safety checks
4. Code cleanup and refactoring
5. Final manual testing

**Deliverables**:
- ✅ Comprehensive test suite
- ✅ All tests passing
- ✅ Performance optimized
- ✅ Bugs fixed
- ✅ Code polished

---

### Phase 8: Documentation (Days 17-18)

**Goals**: Complete documentation for users and developers

See [Documentation Plan](#documentation-plan) below for details.

**Deliverables**:
- ✅ All documentation written
- ✅ Examples tested
- ✅ Diagrams created
- ✅ CLAUDE.md updated

---

## Documentation Plan

### Documentation Structure

```
docs/
├── README.md                  # Main user guide
├── QUICK_START.md             # 5-minute quick start guide
├── CLI_REFERENCE.md           # Complete CLI documentation
├── MARKDOWN_FORMAT.md         # Markdown format specifications
├── CONFIGURATION.md           # Configuration guide
├── WORKFLOWS.md               # Common workflow examples
├── DEVELOPMENT.md             # Developer guide
├── ARCHITECTURE.md            # Architecture documentation
├── CHANGELOG.md               # Version history
└── TROUBLESHOOTING.md         # Common issues and solutions
```

### Documentation Tasks

**Day 17: User Documentation**

1. **README.md** (Main user guide)
   - Project overview
   - Features list
   - Installation instructions
   - Quick start (discover → fetch → process)
   - Basic configuration
   - Usage examples
   - Screenshots (terminal output)

2. **QUICK_START.md** (5-minute guide)
   - Prerequisites
   - Installation (3 steps)
   - First run (discover users)
   - Daily sync workflow
   - Viewing results in Obsidian

3. **CLI_REFERENCE.md** (Complete CLI docs)
   - All commands with full option descriptions
   - Usage examples for each command
   - Common option combinations
   - Error messages and troubleshooting

4. **WORKFLOWS.md** (Common workflows)
   - Daily incremental sync
   - Full historical sync for new user
   - Reprocessing with new AI models
   - Selective processing (specific users/dates)
   - Batch operations
   - Troubleshooting failed messages

5. **MARKDOWN_FORMAT.md** (Format specifications)
   - Staging format specification
   - Processed format specification
   - Field reference table
   - Examples for all message types
   - Obsidian integration tips

6. **CONFIGURATION.md** (Config guide)
   - Complete config.yaml reference
   - Environment variables
   - Provider configuration (Ollama, Claude, Tesseract, Cloud OCR)
   - Customizing prompts
   - Tagging rules
   - Storage settings

**Day 18: Developer Documentation**

7. **DEVELOPMENT.md** (Developer guide)
   - Development setup
   - Code structure overview
   - Adding new processors
   - Adding new AI providers
   - Testing guidelines
   - Contributing guidelines

8. **ARCHITECTURE.md** (Architecture docs)
   - High-level architecture diagram
   - Two-phase processing flow
   - Component interaction diagrams
   - State management design
   - Data flow diagrams

9. **TROUBLESHOOTING.md** (Common issues)
   - Installation issues
   - Telegram connection problems
   - Ollama/AI model issues
   - Media download failures
   - Processing errors
   - Performance issues
   - State corruption recovery

10. **Update CLAUDE.md**
    - New architecture overview
    - Updated commands
    - New file structure
    - Updated common tasks
    - Two-phase workflow explanation

11. **CHANGELOG.md**
    - Version 2.0 release notes
    - Breaking changes
    - Migration notes (N/A - fresh start)
    - New features
    - Improvements

### Documentation Standards

**Writing Style**:
- Clear, concise language
- Step-by-step instructions
- Code examples for all concepts
- Real-world usage scenarios
- Troubleshooting tips in context

**Code Examples**:
- Include comments explaining what's happening
- Show expected output
- Cover edge cases
- Use realistic data

**Diagrams**:
- Architecture diagrams (ASCII art or Mermaid)
- Data flow diagrams
- State transition diagrams
- Directory structure trees

**Screenshots**:
- Terminal output examples
- Progress bars
- Summary reports
- Obsidian integration

---

## Success Criteria

### Functional Requirements

- ✅ All CLI commands working as specified
- ✅ Two-phase architecture fully functional (fetch → staging → process)
- ✅ Staging and processed directories properly maintained
- ✅ Single media folder shared between staging and processed
- ✅ State management tracks both fetch and process states
- ✅ Checksum-based change detection for reprocessing
- ✅ Simple staging markdown format (verbatim text in headers)
- ✅ Enhanced processed markdown format with YAML metadata
- ✅ Automatic tagging (rule-based + optional AI)
- ✅ OCR for images (Tesseract + optional cloud)
- ✅ Link metadata extraction (title + description)
- ✅ Reply context tracking
- ✅ Forward context tracking
- ✅ Edit tracking
- ✅ All existing features preserved (transcription, summarization, YouTube)

### Non-Functional Requirements

- ✅ Performance: Process 100 messages in < 5 minutes (with transcription)
- ✅ Performance: Process 100 messages in < 1 minute (without AI features)
- ✅ Reliability: No data loss, atomic state updates
- ✅ Usability: Clear CLI help, good error messages
- ✅ Maintainability: Clean code, comprehensive tests
- ✅ Documentation: Complete user and developer guides

### Testing Requirements

- ✅ Unit tests: >80% code coverage
- ✅ Integration tests: All major workflows
- ✅ System tests: Real Telegram bot integration
- ✅ Manual testing: All CLI commands tested
- ✅ Performance tests: Benchmarked and optimized

### Documentation Requirements

- ✅ README.md: Clear installation and quick start
- ✅ CLI_REFERENCE.md: Complete command documentation
- ✅ MARKDOWN_FORMAT.md: Format specifications
- ✅ CONFIGURATION.md: Config guide
- ✅ DEVELOPMENT.md: Developer guide
- ✅ CLAUDE.md: Updated for AI assistant
- ✅ All examples tested and working

---

## Risk Mitigation

### State Management Complexity

**Risk**: Two separate states (fetch + process) could lead to sync issues

**Mitigation**:
- Single state.json file with both states
- Atomic updates with file locking
- Backup and rollback on errors
- Comprehensive validation
- State recovery utilities

### Markdown Parsing Fragility

**Risk**: Complex YAML-style format could be fragile

**Mitigation**:
- Robust parsing with error handling
- Schema validation
- Graceful degradation on parse errors
- Keep staging format simple as fallback
- Extensive unit tests for all message types

### Performance with AI Features

**Risk**: Transcription and summarization could be slow

**Mitigation**:
- Parallel processing with configurable workers
- Ability to skip expensive features (--skip-transcription, etc.)
- Incremental processing (only new messages)
- Efficient checksum-based reprocessing
- Progress bars and time estimates

---

## Appendix

### Estimated Timeline

- **Phase 0**: 1 day
- **Phase 1**: 2 days
- **Phase 2**: 2 days
- **Phase 3**: 3 days
- **Phase 4**: 2 days
- **Phase 5**: 2 days
- **Phase 6**: 2 days
- **Phase 7**: 2 days
- **Phase 8**: 2 days

**Total**: 18 days (approximately 3-4 weeks with buffer)

### Key Technologies

- **Python**: 3.11+
- **CLI Framework**: Typer
- **Output Formatting**: Rich
- **Async**: asyncio, aiofiles
- **Config**: PyYAML, python-dotenv
- **Telegram**: aiohttp (for Bot API)
- **Transcription**: Ollama Whisper
- **Summarization**: Ollama (llama2, mistral) or Claude Code CLI
- **OCR**: pytesseract (Tesseract), Google Vision API, Azure CV, AWS Rekognition
- **Link Extraction**: aiohttp, BeautifulSoup4
- **Testing**: pytest, pytest-asyncio

### Dependencies to Add

```toml
[project.dependencies]
typer = {extras = ["all"], version = "^0.9.0"}
rich = "^13.7.0"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
aiohttp = "^3.9.0"
aiofiles = "^23.2.1"
pydantic = "^2.5.0"
beautifulsoup4 = "^4.12.0"
pytesseract = "^0.3.10"
pillow = "^10.1.0"

[project.optional-dependencies]
cloud-ocr = [
    "google-cloud-vision>=3.5.0",
    "azure-cognitiveservices-vision-computervision>=0.9.0",
    "boto3>=1.34.0"
]
```

### File Count Estimate

**New Files**: ~25
**Modified Files**: ~15
**Total Lines of Code**: ~5,000-6,000 (including tests and docs)

---

## Conclusion

This requirements document provides a comprehensive blueprint for Trudy 2.0, covering all architectural decisions, data structures, CLI interface, processing features, and implementation plan. All clarifying questions have been answered, and the design is ready for implementation.

**Next Steps**:
1. Review and approve this requirements document
2. Set up development environment
3. Begin Phase 0 (Preparation)
4. Follow implementation plan sequentially

**Questions or Concerns**:
Please raise any questions or concerns before implementation begins. Once approved, this document will serve as the source of truth for the Trudy 2.0 implementation.
