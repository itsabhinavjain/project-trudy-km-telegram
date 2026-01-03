# Trudy Telegram Note-Taking System

A powerful Telegram bot-based note-taking system that automatically fetches, processes, and organizes your messages into beautifully formatted markdown notes with AI-powered transcription and summarization.

## Features

- **Automatic User Discovery**: Automatically detect and track all users who message your bot
- **Continuous Discovery**: Accumulates users across all runs - never loses track of anyone
- **Multi-User Support**: Handle messages from unlimited Telegram users
- **Rich Media Processing**: Automatically download and organize videos, audio, images, and documents
- **AI Transcription**: Transcribe audio and video using local Whisper models (via Ollama)
- **Smart Summarization**: Generate summaries using Ollama or Claude Code CLI
- **Article Extraction**: Extract and summarize content from article links
- **YouTube Integration**: Fetch transcripts or download YouTube videos with summaries
- **Daily Markdown Files**: Organize notes by date with timestamp headers
- **Incremental Sync**: Only fetch new messages (idempotent operations)
- **Obsidian-Compatible**: Uses wikilink format for easy integration with Obsidian

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Telegram Bot Token (from @BotFather)
- [Ollama](https://ollama.ai/) (for local AI models) - optional
- FFmpeg (for audio/video conversion)

### Installation

1. **Clone the repository**

```bash
cd my-project-trudy-telegram
```

2. **Install dependencies**

```bash
uv sync
```

3. **Install system dependencies**

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Install Ollama (optional, for local AI)
curl https://ollama.ai/install.sh | sh

# Pull models
ollama pull whisper  # For transcription
ollama pull llama2   # For summarization
```

4. **Configure the system**

```bash
# Copy example .env file
cp .env.example .env

# Edit .env and add your Telegram bot token
# That's it! User discovery is automatic.
```

**Note**: The system now automatically discovers users who message your bot. No need to manually configure chat IDs! The `users` section in `config/config.yaml` is now optional and defaults to auto-discovery mode.

### Basic Usage

```bash
# Fetch and process new messages
uv run trudy

# Fetch all historical messages (first run)
uv run trudy --full

# List all discovered users
uv run trudy --discover-users

# Process only specific user
uv run trudy --user john_doe

# Skip summarization (faster)
uv run trudy --no-summarize

# Dry run (preview without writing files)
uv run trudy --dry-run

# Verbose logging
uv run trudy -v
```

## Project Structure

```
my-project-trudy-telegram/
├── src/                    # Source code
│   ├── core/              # Core components (config, logging, state)
│   ├── telegram/          # Telegram API integration
│   ├── processors/        # Message processors
│   ├── ai/                # AI components (transcription, summarization)
│   ├── markdown/          # Markdown formatting and writing
│   └── utils/             # Utilities
├── config/                # Configuration files
├── data/                  # Generated data
│   ├── state.json        # Processing state
│   └── users/            # User-specific notes and media
│       └── <username>/
│           ├── notes/    # Daily markdown files
│           └── media/    # Downloaded media
└── logs/                 # Application logs
```

## Configuration

See `config/config.yaml` for all configuration options:

- **Telegram**: Bot token, API settings
- **Users**: User chat IDs and usernames
- **Transcription**: Ollama/Whisper settings
- **Summarization**: Ollama or Claude Code CLI settings
- **Processing**: Concurrency, error handling
- **Markdown**: Timezone, formatting options

## Documentation

- **[USAGE.md](USAGE.md)**: Detailed usage guide with examples
- **[requirements.md](requirements.md)**: Complete requirements specification

## How It Works

1. **Fetch**: Connect to Telegram Bot API and fetch new messages
2. **Download**: Download any media files (images, videos, audio, documents)
3. **Process**:
   - Transcribe audio/video files using Whisper
   - Extract article content from links
   - Fetch YouTube transcripts or download videos
4. **Summarize**: Generate AI summaries using Ollama or Claude
5. **Write**: Save to daily markdown files with timestamps
6. **Track**: Update state file to remember last processed message

## Example Output

```markdown
# 2026-01-03

## 14:23

**Video Note**

![[2026-01-03_14-23-45_meeting-notes.mp4|Team standup recording]]

**Transcript:** [[2026-01-03_14-23-45_meeting-notes_transcript.txt]]

**Summary:**
- Discussed Q1 roadmap priorities
- Alice to lead the API redesign project
- Sprint planning moved to Fridays

---

## 15:10

**Article: The Future of AI**

https://example.com/ai-article

**Summary:**
Recent advances in AI are transforming how we work...

---
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
