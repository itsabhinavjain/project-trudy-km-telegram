# Quick Start Guide - Trudy 2.0

Get Trudy running in 5 minutes! This guide will help you set up Trudy and sync your first messages.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.11 or higher** installed
- [ ] **uv** package installer ([install here](https://github.com/astral-sh/uv))
- [ ] **Telegram account** and the Telegram app
- [ ] **5 minutes** of your time

Optional (but recommended):
- [ ] **FFmpeg** (for media processing)
- [ ] **Tesseract** (for OCR on images)
- [ ] **Ollama** (for local AI features)

---

## Step 1: Create Your Telegram Bot (2 minutes)

### 1.1 Open Telegram and find @BotFather

Search for **@BotFather** in Telegram (it has a blue checkmark).

### 1.2 Create a new bot

Send this command to @BotFather:
```
/newbot
```

### 1.3 Choose a name and username

- **Name**: `My Personal Bot` (or anything you like)
- **Username**: Must end in "bot" (e.g., `myname_personal_bot`)

### 1.4 Save your bot token

@BotFather will give you a token that looks like:
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**⚠️ Keep this secret!** Anyone with this token can control your bot.

### 1.5 Start a chat with your bot

1. Click the link @BotFather provides
2. Click **START** button
3. Send a test message like "Hello!"

---

## Step 2: Install Trudy (2 minutes)

### 2.1 Clone the repository

```bash
git clone <repository-url>
cd trudy-km-telegram
```

### 2.2 Install Python dependencies

```bash
uv sync
```

This will:
- Create a virtual environment
- Install all required Python packages
- Take ~30 seconds

### 2.3 Set up your bot token

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

Add your bot token:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Save and exit.

---

## Step 3: Run Your First Sync (1 minute)

### 3.1 Sync your messages

```bash
uv run trudy sync
```

You should see:
```
Trudy 2.0 - Full Sync

Phase 1: Fetch
Fetching messages from Telegram... ✓

┌──────────────────────────────────────┐
│ Fetch Results                        │
├──────────┬──────────┬────────────────┤
│ User     │ Chat ID  │ Messages       │
├──────────┼──────────┼────────────────┤
│ myname   │ 12345678 │ 1              │
└──────────┴──────────┴────────────────┘

Phase 2: Process
Processing messages... ✓

Processing Report
  Users: 1
  Messages: 1 processed
  Time: 0.5s

✓ Sync complete!
```

### 3.2 Find your notes

Your messages are now saved as markdown files:

```bash
ls -la data/processed/<your-username>/
```

You'll see files like `2026-01-05.md`

### 3.3 View your first note

```bash
cat data/processed/<your-username>/2026-01-05.md
```

You should see something like:
```markdown
## 14:30 - Hello!
type: text
content: |-
  Hello!
tags: [#greeting]

---
```

---

## Next Steps

### Daily Usage

From now on, just run this command daily (or whenever you want):

```bash
uv run trudy sync
```

It will:
1. Fetch any new messages since last sync
2. Process them through the AI pipeline
3. Add them to your daily notes

### Send Different Types of Messages

Try sending to your bot:
- **Text**: "Remember to buy milk"
- **Image**: Any photo
- **Link**: https://example.com/article
- **Voice**: Record a voice message
- **File**: Any document

Then run `uv run trudy sync` and see how each appears in your notes!

---

## Optional: Install AI Features

For the best experience, install optional AI tools:

### FFmpeg (Required for media)

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/)

### Tesseract (For OCR on images)

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Ollama (For transcription & summarization)

**All platforms:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull AI models
ollama pull whisper  # For audio/video transcription
ollama pull llama2   # For text summarization
```

Then run sync again:
```bash
uv run trudy sync
```

Now your voice messages will be transcribed and long articles summarized!

---

## Optional: Obsidian Integration

If you use Obsidian:

### 1. Configure Obsidian vault path

Edit `config/config.yaml`:
```yaml
storage:
  base_dir: "/path/to/your/obsidian/vault/Trudy"

markdown:
  wikilink_style: "obsidian"
```

### 2. Sync

```bash
uv run trudy sync
```

### 3. Open Obsidian

Your Trudy notes will appear in your vault with:
- Wikilink-style media embeds: `![[image.jpg]]`
- Clickable tags
- Full-text search

---

## Troubleshooting

### "Bot token is invalid"
- Double-check your token in `.env`
- Make sure there are no spaces or quotes around it
- Verify you sent `/start` to your bot

### "No messages found"
- Send a message to your bot first
- Click "START" in the bot chat
- Wait a few seconds and try again

### "Command not found: trudy"
- Use `uv run trudy` instead of just `trudy`
- Make sure you're in the project directory

### "Permission denied"
- Make sure the `data/` directory is writable
- Check file permissions: `ls -la data/`

### Still stuck?
See [Troubleshooting Guide](TROUBLESHOOTING.md) for more help.

---

## What's Next?

Now that you're up and running:

1. **Read the [CLI Reference](CLI_REFERENCE.md)** - Learn all commands
2. **Check out [Workflows](WORKFLOWS.md)** - Common usage patterns
3. **Customize [Configuration](CONFIGURATION.md)** - Tailor to your needs
4. **Explore [Markdown Formats](MARKDOWN_FORMAT.md)** - Understand the output

---

## Pro Tips

### Faster Syncing

Skip AI features for instant results:
```bash
uv run trudy sync --skip-transcription --skip-ocr --skip-summarization
```

### Specific User Only

If multiple people message your bot:
```bash
uv run trudy sync --user yourname
```

### Full Historical Sync

Get all old messages:
```bash
uv run trudy sync --full
```

### Verbose Output

See what's happening:
```bash
uv run trudy sync -v
```

### Dry Run

Preview without writing files:
```bash
uv run trudy sync --dry-run
```

---

## Quick Reference Card

Save this for daily use:

```bash
# Daily sync
uv run trudy sync

# Fast sync (no AI)
uv run trudy sync --skip-transcription --skip-ocr --skip-summarization

# Force reprocess
uv run trudy process --reprocess

# Get help
uv run trudy --help

# Check version
uv run trudy --version
```

---

**Congratulations! 🎉**

You're now using Trudy 2.0. Send messages to your bot and watch them transform into organized knowledge!

**Happy note-taking! 📚✨**
