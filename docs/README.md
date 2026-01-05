# Trudy 2.0 - Personal Knowledge Management Bot

Transform your Telegram messages into organized, enriched markdown notes with AI-powered features.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Overview

Trudy 2.0 is a powerful Telegram bot-based system that automatically captures, processes, and organizes your messages into beautifully formatted markdown notes. Perfect for:

- 📝 **Personal note-taking** - Send yourself notes via Telegram
- 📚 **Knowledge management** - Organize thoughts, ideas, and research
- 🎯 **Task tracking** - Quick todos and reminders
- 📸 **Media archival** - Store photos, videos, documents with OCR
- 🔗 **Link curation** - Save articles with auto-summaries
- 🎙️ **Voice notes** - Transcribe audio and video messages
- 🏷️ **Auto-organization** - Automatic tagging and categorization

### What's New in v2.0

- ✨ **Two-Phase Architecture** - Separate fetching from processing for atomic operations
- 🔄 **Reprocessing** - Change AI settings and reprocess without re-fetching
- 📊 **Rich Metadata** - YAML frontmatter with tags, summaries, OCR, and more
- 🏷️ **Auto-Tagging** - Intelligent tag generation from content
- 🔍 **OCR Support** - Extract text from images (Tesseract)
- 🔗 **Link Metadata** - Automatic title and description extraction
- 💬 **Context Tracking** - Preserve replies, forwards, and edit history
- 🎨 **Modern CLI** - Beautiful terminal UI with progress bars
- ✅ **Checksum-Based** - Only reprocess when files change

---

## Quick Links

- [Quick Start Guide](QUICK_START.md) - Get running in 5 minutes
- [CLI Reference](CLI_REFERENCE.md) - All commands and options
- [Configuration Guide](CONFIGURATION.md) - Complete config reference
- [Workflows](WORKFLOWS.md) - Common usage patterns
- [Troubleshooting](TROUBLESHOOTING.md) - Problem solving

---

## Features

### Core Functionality

#### Two-Phase Processing
```
Phase 1: Fetch → Staging        Phase 2: Staging → Processed
┌─────────────────────┐          ┌─────────────────────┐
│ Telegram Bot API    │          │ Staging Files       │
│ ↓                   │          │ ↓                   │
│ Fetch new messages  │   →      │ Parse & process     │
│ Download media      │          │ Apply AI features   │
│ Write to staging/   │          │ Generate rich output│
└─────────────────────┘          └─────────────────────┘
```

#### Message Types Supported
- ✅ **Text** - Plain text messages
- ✅ **Images** - Photos with optional OCR
- ✅ **Videos** - Videos with transcription support
- ✅ **Audio** - Audio files with transcription
- ✅ **Voice** - Voice messages with transcription
- ✅ **Documents** - PDFs, files, etc.
- ✅ **Links** - URLs with metadata extraction
- ✅ **YouTube** - Videos with transcript fetching

### AI-Powered Enrichment

#### 🎙️ Transcription
- Automatic transcription of audio and video messages
- Powered by Ollama Whisper (local, private)
- Supports multiple languages
- Saves transcripts as separate files

#### 📝 Summarization
- AI-generated summaries for long content
- Works with articles, videos, transcripts
- Choose between Ollama (local) or Claude (high quality)
- Customizable prompts

#### 🔍 OCR (Optical Character Recognition)
- Extract text from images automatically
- Powered by Tesseract (local, free)
- Support for multiple languages
- Cloud OCR providers (Google Vision, Azure, AWS) coming soon

#### 🏷️ Auto-Tagging
- Rule-based tagging with regex patterns
- AI-powered tag suggestions (coming soon)
- Automatic media type tags (#image, #video, etc.)
- Feature-based tags (#ocr, #transcription, #summarized)

#### 🔗 Link Metadata
- Automatic title extraction from web pages
- Meta description capture
- OpenGraph support
- Favicon extraction (optional)

### Organization & Storage

#### Smart File Organization
```
data/
├── staging/          # Raw messages (simple format)
│   ├── alice/
│   │   └── 2026-01-05.md
│   └── bob/
│       └── 2026-01-05.md
│
├── processed/        # Enriched notes (YAML metadata)
│   ├── alice/
│   │   └── 2026-01-05.md
│   └── bob/
│       └── 2026-01-05.md
│
└── media/            # Shared media folder
    ├── alice/
    │   ├── image.jpg
    │   └── video_transcript.txt
    └── bob/
        └── document.pdf
```

#### Incremental Sync
- Tracks last processed message per user
- Only fetches new messages (efficient)
- State persistence across runs
- Safe interruption and resumption

#### Checksum-Based Reprocessing
- SHA-256 checksums detect file changes
- Skip unchanged files (fast)
- Only reprocess when needed
- Force reprocess with `--reprocess` flag

---

## Installation

### Prerequisites

- **Python 3.11+**
- **Telegram Bot** (get token from [@BotFather](https://t.me/BotFather))
- **uv** (Python package installer)
- **FFmpeg** (for media processing)
- **Tesseract** (for OCR, optional)
- **Ollama** (for AI features, optional)

### System Dependencies

#### macOS
```bash
brew install ffmpeg
brew install tesseract  # For OCR
brew install ollama      # For local AI
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install ffmpeg
sudo apt-get install tesseract-ocr
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
- Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/)
- Download Tesseract from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Install Ollama from [ollama.ai](https://ollama.ai/)

### Python Dependencies

```bash
# Clone repository
git clone <repository-url>
cd trudy-km-telegram

# Install Python dependencies with uv
uv sync

# Pull AI models (optional)
ollama pull whisper  # For transcription
ollama pull llama2   # For summarization
```

### Configuration

1. **Copy example environment file:**
```bash
cp .env.example .env
```

2. **Edit `.env` and add your bot token:**
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

3. **Review `config/config.yaml`** (optional)
   - Adjust timezone
   - Configure AI providers
   - Set storage paths
   - Customize tagging rules

See [Configuration Guide](CONFIGURATION.md) for complete reference.

---

## Usage

### Basic Workflow

#### 1. Send yourself a message on Telegram
Open your bot on Telegram and send any message.

#### 2. Run sync command
```bash
uv run trudy sync
```

This will:
- Fetch messages from Telegram
- Download any media files
- Process through AI pipeline
- Generate enriched markdown notes

#### 3. View your notes
Notes are saved in `data/processed/<username>/YYYY-MM-DD.md`

Open in your favorite markdown editor (Obsidian, VSCode, etc.)

### Common Commands

```bash
# Full sync (most common)
uv run trudy sync

# Sync specific user
uv run trudy sync --user alice

# Full historical sync
uv run trudy sync --full

# Quick sync without AI (faster)
uv run trudy sync --skip-transcription --skip-ocr --skip-summarization

# Fetch only (Phase 1)
uv run trudy fetch

# Process only (Phase 2)
uv run trudy process

# Reprocess with new AI settings
uv run trudy process --reprocess

# Get help
uv run trudy --help
uv run trudy sync --help
```

See [CLI Reference](CLI_REFERENCE.md) for all commands.

---

## Output Examples

### Staging Format (Simple)
```markdown
## 14:30 - Hello, this is a test message

Hello, this is a test message

---

## 14:35 - [Image]

![Image](../media/alice/2026-01-05_14-35-20_image.jpg)

Caption: Beautiful sunset

---
```

### Processed Format (Rich YAML)
```markdown
## 14:35 - [Image]
type: image
file: ![[2026-01-05_14-35-20_image.jpg]]
caption: |-
  Beautiful sunset
ocr_text: |-
  SUNSET BEACH
  PHOTOGRAPHY BY ALICE
tags: [#image, #ocr, #nature]
reply_to:
  message_id: 4566
  timestamp: "2026-01-05T14:30:00"
  preview: "What a beautiful day!"

---
```

See [Markdown Format Guide](MARKDOWN_FORMAT.md) for complete specification.

---

## Integration

### Obsidian

Trudy 2.0 is designed to work seamlessly with Obsidian:

1. **Set Obsidian vault as base directory:**
```yaml
# config/config.yaml
storage:
  base_dir: "/path/to/obsidian/vault/Trudy"
```

2. **Use Obsidian wikilinks:**
```yaml
# config/config.yaml
markdown:
  wikilink_style: "obsidian"
```

3. **Sync regularly:**
```bash
# Add to cron or run manually
uv run trudy sync
```

Your messages will appear as daily notes with:
- Wikilink-style media embeds: `![[image.jpg]]`
- Clickable tags: `#tag`
- Linked transcripts
- Full-text search

### Other Markdown Editors

Works with any markdown editor:
- VSCode with Markdown Preview
- Typora
- Mark Text
- iA Writer

Just use standard markdown style:
```yaml
markdown:
  wikilink_style: "markdown"
```

---

## Workflows

### Daily Note-Taking
```bash
# Morning: Send yourself todos and notes via Telegram throughout the day
# Evening: Sync to markdown
uv run trudy sync

# Notes appear in data/processed/<your-username>/YYYY-MM-DD.md
```

### Research & Article Curation
```bash
# Send article links to your bot
# Trudy extracts title, description, and generates summary

uv run trudy sync

# Articles appear with rich metadata and summaries
```

### Voice Note Journaling
```bash
# Record voice messages on Telegram
# Trudy transcribes automatically

uv run trudy sync

# Voice notes appear with full transcripts
```

### Screenshot & Image Organization
```bash
# Send screenshots or photos to your bot
# Trudy extracts text with OCR

uv run trudy sync

# Images appear with extracted text for full-text search
```

See [Workflows Guide](WORKFLOWS.md) for more examples.

---

## Configuration

### Basic Settings

#### Timezone
```yaml
markdown:
  timezone: "America/New_York"
```

#### AI Providers
```yaml
transcription:
  enabled: true
  provider: "ollama"  # or "remote"

summarization:
  enabled: true
  provider: "ollama"  # or "claude"

ocr:
  enabled: true
  provider: "tesseract"  # or "cloud"
```

#### Storage
```yaml
storage:
  base_dir: "./data"
  staging_retention:
    policy: "keep_days"  # or "keep_all", "delete_after_process"
    days: 7
```

See [Configuration Guide](CONFIGURATION.md) for complete reference.

---

## Troubleshooting

### Common Issues

**Bot not responding:**
- Check bot token in `.env`
- Ensure bot is started (send `/start` command)
- Verify network connection

**OCR not working:**
```bash
# Check Tesseract installation
tesseract --version

# Install if missing
brew install tesseract  # macOS
```

**Ollama connection failed:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve
```

**State corruption:**
```bash
# State is backed up automatically
# Restore from backup if needed
cp data/state.json.backup data/state.json
```

See [Troubleshooting Guide](TROUBLESHOOTING.md) for complete solutions.

---

## Performance

### Benchmarks (typical usage)

- **Fetch Phase:** ~100 messages/minute
- **Process Phase (with AI):** ~20 messages/minute
- **Process Phase (without AI):** ~500 messages/minute
- **Reprocess (unchanged files):** ~1000 messages/minute (skipped)

### Optimization Tips

```bash
# Skip expensive AI features for speed
uv run trudy sync --skip-transcription --skip-summarization

# Process in parallel (future feature)
uv run trudy process --workers 5

# Use local Ollama instead of cloud APIs
# (faster, private, no API costs)
```

---

## Architecture

### Two-Phase Design

**Phase 1: Fetch → Staging**
- Connect to Telegram Bot API
- Fetch new messages (incremental)
- Download media to shared folder
- Write simple markdown to `staging/`
- Update `fetch_state`

**Phase 2: Staging → Processed**
- Read pending staging files
- Calculate checksums (detect changes)
- Parse messages from staging
- Process through AI pipeline
- Write enriched markdown to `processed/`
- Update `process_state`

### Benefits

- ✅ **Atomic Operations** - Fetch and process can fail independently
- ✅ **Reprocessing** - Change AI settings without re-fetching
- ✅ **Debugging** - Inspect staging files before processing
- ✅ **Performance** - Skip unchanged files with checksums
- ✅ **Flexibility** - Different workflows for different needs

See [Architecture Guide](ARCHITECTURE.md) for technical details.

---

## Development

### Contributing

Contributions are welcome! See [Development Guide](DEVELOPMENT.md) for:
- Development environment setup
- Code structure
- Adding new processors
- Adding new AI providers
- Testing guidelines

### Project Structure

```
trudy-km-telegram/
├── src/
│   ├── cli/          # Typer CLI commands
│   ├── core/         # Core logic (state, config, processor)
│   ├── telegram/     # Telegram API integration
│   ├── processors/   # Message processors
│   ├── ai/           # AI features (OCR, tagging, etc.)
│   ├── markdown/     # Markdown writers/readers
│   └── utils/        # Utilities
├── config/
│   └── config.yaml   # Configuration file
├── docs/             # Documentation
├── tests/            # Tests
└── data/             # Generated data (gitignored)
```

---

## Support

### Getting Help

- 📖 **Documentation:** Start with [Quick Start Guide](QUICK_START.md)
- 🐛 **Issues:** Report bugs on GitHub Issues
- 💬 **Discussions:** Ask questions on GitHub Discussions
- 📧 **Email:** Contact maintainer

### Useful Resources

- [CLI Reference](CLI_REFERENCE.md) - All commands
- [Configuration Guide](CONFIGURATION.md) - All settings
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common problems
- [CLAUDE.md](../CLAUDE.md) - Developer guide for AI assistants

---

## License

MIT License - See LICENSE file for details

---

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.

---

## Acknowledgments

Built with:
- [Python Telegram Bot](https://python-telegram-bot.org/)
- [Typer](https://typer.tiangolo.com/)
- [Rich](https://rich.readthedocs.io/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Ollama](https://ollama.ai/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

---

**Trudy 2.0** - Transform your messages into knowledge 📚✨
