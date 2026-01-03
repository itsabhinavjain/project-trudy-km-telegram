

# Trudy Telegram - Usage Guide

This guide provides detailed instructions on how to use the Trudy Telegram note-taking system.

## Table of Contents

- [Setup](#setup)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Message Types](#message-types)
- [CLI Commands](#cli-commands)
- [Workflow Examples](#workflow-examples)
- [Troubleshooting](#troubleshooting)

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Choose a name and username for your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure the System

```bash
cp .env.example .env
# Edit .env and add your bot token
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**That's it!** The system now automatically discovers users who send messages to your bot.

### 3. Understanding Auto-Discovery

**How it works:**
- When you run `uv run trudy`, the system fetches all messages from your bot
- It automatically discovers which users have messaged the bot
- **Continuous Discovery**: Users are accumulated across all runs
  - Day 1: 3 users message → 3 users tracked in state.json
  - Day 2: 4 new users + 1 old user → All 7 users tracked
  - The system remembers all users who have ever interacted with the bot
- Usernames are generated from:
  1. Telegram username (if available) - e.g., `@john_doe` becomes `john_doe`
  2. First name + Last name - e.g., "John Doe" becomes `john_doe`
  3. User ID as fallback - e.g., `user_123456789`

**Optional Manual Configuration:**
If you want to control the exact usernames used for folder organization, you can manually configure users in `config/config.yaml`:

```yaml
users:
  - username: "john_doe"  # Custom username for folder organization
    phone: "+1234567890"  # Optional
    chat_id: 123456789     # Get from: https://api.telegram.org/bot<TOKEN>/getUpdates
```

Leave it as `users: []` for auto-discovery (recommended).

### 4. Send a Test Message

Send any message to your bot on Telegram to make sure it's working. The system will discover you as a user automatically when you run it.

### 5. Install Dependencies

```bash
# Install Python dependencies
uv sync

# Install system dependencies (macOS)
brew install ffmpeg

# Install and setup Ollama (optional, for local AI)
curl https://ollama.ai/install.sh | sh
ollama pull whisper
ollama pull llama2
```

## Configuration

### User Discovery Modes

Trudy supports two modes for managing users:

#### Auto-Discovery Mode (Default & Recommended)

Set in `config/config.yaml`:
```yaml
users: []
```

**Benefits:**
- No manual configuration needed
- Automatically handles new users
- Works with any number of users
- Generates sensible usernames automatically
- Continuously tracks all users across runs

**How usernames are generated:**
1. From Telegram `@username` (e.g., `@john_doe` → `john_doe`)
2. From name (e.g., "John Doe" → `john_doe`)
3. From user ID (e.g., User 123 → `user_123`)

**Example output:**
```
Auto-discovering users from bot messages...
Discovered 2 new users
Total users: 7, New messages: 15
```

**Listing all discovered users:**
```bash
# Use --discover-users to see all users without processing messages
uv run trudy --discover-users

# Output:
Discovered 7 users:

  • john_doe
    Chat ID: 123456789
    Total messages: 42
    First message: 2026-01-01 10:00:00
    Last fetch: 2026-01-03 18:30:00
  ...
```

#### Manual Configuration Mode

Set in `config/config.yaml`:
```yaml
users:
  - username: "my_custom_name"
    chat_id: 123456789
    phone: "+1234567890"  # optional
```

**Benefits:**
- Full control over usernames
- Can add metadata (phone numbers)
- Restrict to specific users only

**Use when:**
- You want custom folder names
- You want to filter specific users
- You need to maintain consistent naming

### Telegram Settings

```yaml
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # From .env
  timeout: 30
  retry_attempts: 3
```

### Transcription Settings

```yaml
transcription:
  enabled: true
  provider: "ollama"  # or "remote"
  ollama:
    base_url: "http://localhost:11434"
    model: "whisper"
  youtube_prefer_transcript: true  # Use YouTube API first
```

### Summarization Settings

```yaml
summarization:
  enabled: true
  provider: "ollama"  # Options: "ollama" or "claude"

  # For Ollama
  ollama:
    model: "llama2"  # or "mistral", "phi", etc.
    temperature: 0.7
    max_tokens: 500

  # For Claude Code CLI
  claude:
    cli_path: "claude"
    model: "claude-sonnet-4-5"
    max_tokens: 1000
```

### Storage Settings

```yaml
storage:
  base_dir: "./data"
  notes_subdir: "notes"
  media_subdir: "media"
```

### Markdown Settings

```yaml
markdown:
  timezone: "America/New_York"  # Your timezone
  timestamp_format: "HH:MM"
  wikilink_style: "obsidian"
```

## Basic Usage

### First Run (Fetch All Messages)

```bash
uv run trudy --full
```

This will:
- Fetch all historical messages from your Telegram bot
- Download all media files
- Transcribe audio/video
- Generate summaries
- Create daily markdown files

### Regular Runs (Fetch New Messages Only)

```bash
uv run trudy
```

This will:
- Fetch only new messages since last run
- Process them the same way
- Update state file

### Process Specific User

```bash
uv run trudy --user john_doe
```

### Skip Summarization (Faster)

```bash
uv run trudy --no-summarize
```

Useful when:
- You want faster processing
- You're testing the system
- You'll add summaries later

### Dry Run (Preview Mode)

```bash
uv run trudy --dry-run
```

Shows what would be processed without writing files.

### Verbose Logging

```bash
uv run trudy -v
```

Enables DEBUG-level logging for troubleshooting.

## Message Types

### Text Messages

Simply send text to your bot. It will be saved in the daily markdown file.

**Example:**
```
Remember to buy groceries
```

**Output:**
```markdown
## 14:23

Remember to buy groceries
```

### Images/Photos

Send images with optional captions.

**Output:**
```markdown
## 14:25

**Image**

![[2026-01-03_14-25-30_screenshot.jpg|Caption text]]
```

### Videos

Send videos - they will be downloaded and transcribed.

**Output:**
```markdown
## 14:30

**Video Note**

![[2026-01-03_14-30-15_meeting.mp4|Team meeting]]

**Transcript:** [[2026-01-03_14-30-15_meeting_transcript.txt]]

**Summary:**
- Discussed project timeline
- Assigned tasks to team members
```

### Audio/Voice Messages

Audio files and voice messages are transcribed.

**Output:**
```markdown
## 15:00

**Audio Recording**

![[2026-01-03_15-00-22_ideas.mp3]]

**Transcript:** [[2026-01-03_15-00-22_ideas_transcript.txt]]

**Summary:**
Notes on product improvements...
```

### Article Links

Send article URLs for extraction and summarization.

**Example:**
```
https://example.com/interesting-article
```

**Output:**
```markdown
## 16:00

**Article: The Future of Work**

https://example.com/interesting-article

*Author: Jane Doe | Published: 2026-01-01*

**Summary:**
The article discusses how remote work is transforming...
```

### YouTube Links

Send YouTube URLs - transcript will be fetched or video downloaded.

**Example:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Output:**
```markdown
## 17:00

**YouTube: How to Build AI Apps**

https://www.youtube.com/watch?v=dQw4w9WgXcQ

*Channel: Tech Tutorial*

**Transcript:** [[2026-01-03_17-00-45_How-to-Build-AI-Apps_transcript.txt]]

**Summary:**
The video covers key concepts in AI development...
```

### Documents

Send PDFs, Word docs, etc. - they will be downloaded and linked.

**Output:**
```markdown
## 18:00

**Document**

![[2026-01-03_18-00-12_report.pdf]]
```

## CLI Commands

### Full Command Reference

```bash
uv run trudy [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--config PATH` | `-c` | Path to config file (default: config/config.yaml) |
| `--full` | | Fetch all historical messages |
| `--user USERNAME` | `-u` | Process only this user |
| `--dry-run` | | Preview mode, don't write files |
| `--no-summarize` | | Skip AI summarization |
| `--verbose` | `-v` | Enable verbose logging |
| `--discover-users` | | List all discovered users without processing messages |
| `--help` | | Show help message |

### Examples

```bash
# Full sync for all users
uv run trudy --full

# Incremental sync (default)
uv run trudy

# List all discovered users
uv run trudy --discover-users

# Process only john_doe
uv run trudy --user john_doe

# Fast mode without summaries
uv run trudy --no-summarize

# Preview without writing
uv run trudy --dry-run

# Debug mode
uv run trudy -v

# Combine options
uv run trudy --user jane_doe --no-summarize -v
```

## Workflow Examples

### Daily Workflow

1. **Morning**: Send notes to your Telegram bot throughout the day
2. **Evening**: Run `uv run trudy` to process the day's messages
3. **Review**: Open daily markdown file in Obsidian or your editor

### Meeting Notes Workflow

1. **During meeting**: Record audio on phone
2. **Send**: Share audio to your Telegram bot
3. **Process**: Run `uv run trudy`
4. **Result**: Get transcribed and summarized meeting notes

### Article Reading Workflow

1. **Find article**: See interesting article on web or phone
2. **Share**: Send link to your Telegram bot
3. **Process**: Run `uv run trudy`
4. **Result**: Get extracted article with AI summary

### YouTube Learning Workflow

1. **Watch**: Find educational YouTube video
2. **Save**: Send link to your Telegram bot
3. **Process**: Run `uv run trudy`
4. **Result**: Get transcript and summary for future reference

## File Organization

After running Trudy, your files will be organized as:

```
data/
├── state.json              # Tracks processing state
└── users/
    ├── john_doe/
    │   ├── notes/
    │   │   ├── 2026-01-03.md      # Daily markdown files
    │   │   ├── 2026-01-04.md
    │   │   └── 2026-01-05.md
    │   └── media/
    │       ├── 2026-01-03_14-23-45_photo.jpg
    │       ├── 2026-01-03_14-30-15_video.mp4
    │       ├── 2026-01-03_14-30-15_video_transcript.txt
    │       └── ...
    └── jane_doe/
        ├── notes/
        └── media/
```

## Troubleshooting

### Bot not receiving messages

1. Make sure you've sent `/start` to your bot
2. Verify bot token is correct in `.env`
3. Check bot is not blocked

### No messages fetched

1. Verify chat_id is correct in config.yaml
2. Try `--full` flag for first run
3. Check logs in `logs/trudy.log`

### Transcription not working

1. Ensure Ollama is running: `ollama list`
2. Pull whisper model: `ollama pull whisper`
3. Check FFmpeg is installed: `ffmpeg -version`

### Summarization failing

For Ollama:
```bash
ollama list  # Check model is installed
ollama pull llama2  # Install if missing
```

For Claude Code:
```bash
which claude  # Verify CLI is in PATH
```

### Media files not downloading

1. Check disk space
2. Verify media directory permissions
3. Check Telegram file size limits (20MB for bot API)

### State file corrupted

The state file tracks processed messages. If corrupted:

```bash
# Backup current state
cp data/state.json data/state.json.backup

# Delete and re-run with --full
rm data/state.json
uv run trudy --full
```

## Advanced Usage

### Custom Configuration File

```bash
uv run trudy --config /path/to/custom-config.yaml
```

### Running as Cron Job

Add to crontab:

```bash
# Run every hour
0 * * * * cd /path/to/trudy && /path/to/uv run trudy >> /var/log/trudy-cron.log 2>&1
```

### Integration with Obsidian

1. Set `storage.base_dir` to your Obsidian vault location
2. Enable Obsidian wikilink style in config
3. Files will appear directly in your vault

## Tips & Best Practices

1. **Regular Sync**: Run `uv run trudy` daily or set up cron
2. **Start Small**: Test with a few messages before full sync
3. **Use Dry Run**: Preview with `--dry-run` before committing
4. **Monitor Logs**: Check `logs/trudy.log` for issues
5. **Backup State**: Keep `data/state.json` backed up
6. **Clear Captions**: Add descriptive captions to media
7. **Organize**: Use consistent naming in messages

## Getting Help

- Check logs: `logs/trudy.log` and `logs/errors.log`
- Use verbose mode: `uv run trudy -v`
- Review configuration: `config/config.yaml`
- Check state: `data/state.json`
