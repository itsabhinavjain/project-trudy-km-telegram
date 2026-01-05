# CLI Reference - Trudy 2.0

Complete reference for all Trudy commands, options, and usage patterns.

---

## Table of Contents

- [Global Options](#global-options)
- [Commands Overview](#commands-overview)
- [fetch](#fetch-command) - Fetch messages from Telegram
- [process](#process-command) - Process staging files
- [sync](#sync-command) - Combined fetch + process
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)

---

## Global Options

These options work with all commands:

### `--config`, `-c`
Specify configuration file path.

**Default:** `config/config.yaml`

**Example:**
```bash
uv run trudy --config /path/to/config.yaml sync
```

### `--verbose`, `-v`
Enable verbose (DEBUG level) logging.

**Example:**
```bash
uv run trudy -v sync
```

### `--quiet`, `-q`
Suppress non-error output.

**Example:**
```bash
uv run trudy -q sync
```

### `--version`
Show version and exit.

**Example:**
```bash
uv run trudy --version
# Output: Trudy version 2.0.0
```

### `--help`
Show help message and exit.

**Example:**
```bash
uv run trudy --help
```

---

## Commands Overview

| Command | Purpose | Phase |
|---------|---------|-------|
| `fetch` | Fetch messages from Telegram to staging | Phase 1 |
| `process` | Process staging files to enriched markdown | Phase 2 |
| `sync` | Combined fetch + process workflow | Both |

---

## `fetch` Command

Fetch messages from Telegram Bot API and write to staging area.

### Synopsis

```bash
uv run trudy fetch [OPTIONS] [USERS...]
```

### Description

The `fetch` command implements **Phase 1** of the two-phase workflow:
1. Connects to Telegram Bot API
2. Discovers users (auto-discovery mode)
3. Fetches new messages (incremental sync by default)
4. Downloads media to shared `media/` folder
5. Writes messages to `staging/` area
6. Updates `fetch_state` in state.json

### Positional Arguments

#### `USERS...` (optional)
Specific usernames to fetch. Leave empty for all users.

**Example:**
```bash
uv run trudy fetch alice bob
```

### Options

#### `--all` (default: true)
Fetch for all discovered users.

**Example:**
```bash
uv run trudy fetch --all
```

#### `--user USERNAME`, `-u USERNAME` (repeatable)
Fetch for specific user. Can be used multiple times.

**Example:**
```bash
uv run trudy fetch --user alice --user bob
```

#### `--full`
Full sync - fetch all historical messages, ignoring `last_message_id`.

**Default:** Incremental sync (only new messages)

**Example:**
```bash
uv run trudy fetch --full
```

**⚠️ Warning:** This can take a long time and fetch many messages!

#### `--limit INTEGER`
Limit number of messages to fetch per user.

**Example:**
```bash
uv run trudy fetch --limit 100
```

#### `--dry-run`
Preview what would be fetched without writing files.

**Example:**
```bash
uv run trudy fetch --dry-run
```

### Examples

#### Fetch new messages for all users (incremental)
```bash
uv run trudy fetch
```

#### Fetch for specific user
```bash
uv run trudy fetch --user alice
```

#### Full historical sync
```bash
uv run trudy fetch --full
```

#### Preview without writing
```bash
uv run trudy fetch --dry-run -v
```

#### Fetch last 50 messages only
```bash
uv run trudy fetch --limit 50
```

### Output

Shows a table with fetch results:

```
Fetch Results
┌──────────┬──────────┬──────────────────┐
│ User     │ Chat ID  │ Messages Fetched │
├──────────┼──────────┼──────────────────┤
│ alice    │ 12345678 │ 5                │
│ bob      │ 87654321 │ 3                │
└──────────┴──────────┴──────────────────┘

Total: 2 users, 8 messages fetched
```

### Files Created

- `data/staging/<username>/YYYY-MM-DD.md` - Staging markdown files
- `data/media/<username>/*` - Downloaded media files
- `data/state.json` - Updated with fetch state

### Exit Codes

- `0` - Success
- `1` - Error occurred
- `130` - Interrupted by user (Ctrl+C)

---

## `process` Command

Process staging files and generate enriched markdown with YAML metadata.

### Synopsis

```bash
uv run trudy process [OPTIONS] [USERS...]
```

### Description

The `process` command implements **Phase 2** of the two-phase workflow:
1. Reads pending staging files
2. Calculates checksums (detects changes)
3. Parses messages from staging markdown
4. Processes through processor chain
5. Applies AI features (OCR, transcription, summarization, tagging)
6. Extracts link metadata
7. Writes enriched markdown to `processed/`
8. Updates `process_state` with checksums

### Positional Arguments

#### `USERS...` (optional)
Specific usernames to process. Leave empty for all users.

**Example:**
```bash
uv run trudy process alice bob
```

### Options

#### `--all` (default: true)
Process all users with pending files.

**Example:**
```bash
uv run trudy process --all
```

#### `--user USERNAME`, `-u USERNAME` (repeatable)
Process specific user. Can be used multiple times.

**Example:**
```bash
uv run trudy process --user alice --user bob
```

#### `--date DATE`
Process specific date only (format: YYYY-MM-DD).

**Example:**
```bash
uv run trudy process --date 2026-01-05
```

#### `--skip-transcription`
Skip audio/video transcription.

**Use when:** You don't need transcripts or want faster processing.

**Example:**
```bash
uv run trudy process --skip-transcription
```

#### `--skip-ocr`
Skip OCR text extraction from images.

**Use when:** You don't need text from images or want faster processing.

**Example:**
```bash
uv run trudy process --skip-ocr
```

#### `--skip-summarization`
Skip AI summarization.

**Use when:** You don't need summaries or want faster processing.

**Example:**
```bash
uv run trudy process --skip-summarization
```

#### `--skip-tags`
Skip automatic tag generation.

**Example:**
```bash
uv run trudy process --skip-tags
```

#### `--skip-links`
Skip link metadata extraction.

**Example:**
```bash
uv run trudy process --skip-links
```

#### `--reprocess`
Force reprocessing even if files haven't changed.

**Use when:**
- You changed AI models or prompts
- You want to regenerate summaries/tags
- You updated tagging rules

**Example:**
```bash
uv run trudy process --reprocess
```

#### `--workers INTEGER` (default: 3)
Number of parallel processing workers.

**Note:** Not fully implemented yet.

**Example:**
```bash
uv run trudy process --workers 5
```

#### `--dry-run`
Preview what would be processed without writing files.

**Example:**
```bash
uv run trudy process --dry-run
```

### Examples

#### Process pending files
```bash
uv run trudy process
```

#### Process specific user
```bash
uv run trudy process --user alice
```

#### Fast processing (skip all AI)
```bash
uv run trudy process --skip-transcription --skip-ocr --skip-summarization
```

#### Reprocess with new summarization prompt
```bash
# Edit config/config.yaml to change prompt
# Then:
uv run trudy process --reprocess
```

#### Process specific date
```bash
uv run trudy process --date 2026-01-04
```

#### Preview without writing
```bash
uv run trudy process --dry-run -v
```

### Output

Shows processing report:

```
Processing Report

┌────────────────────┬────────┐
│ Metric             │ Value  │
├────────────────────┼────────┤
│ Users processed    │ 2      │
│ Files processed    │ 4      │
│ Messages processed │ 15     │
│ Messages skipped   │ 5      │
│                    │        │
│ Transcriptions     │ 2      │
│ OCR performed      │ 3      │
│ Summaries generated│ 1      │
│ Tags generated     │ 45     │
│ Links extracted    │ 5      │
│                    │        │
│ Errors             │ 0      │
│ Time elapsed       │ 12.5s  │
└────────────────────┴────────┘
```

### Files Created

- `data/processed/<username>/YYYY-MM-DD.md` - Enriched markdown files
- `data/media/<username>/*_transcript.txt` - Transcript files (if any)

### Files Modified

- `data/state.json` - Updated with process state and checksums

### Exit Codes

- `0` - Success (or no pending files)
- `1` - Errors occurred during processing
- `130` - Interrupted by user (Ctrl+C)

---

## `sync` Command

Combined fetch + process workflow. Most commonly used command.

### Synopsis

```bash
uv run trudy sync [OPTIONS] [USERS...]
```

### Description

The `sync` command runs both phases in sequence:
1. **Phase 1:** Fetch messages from Telegram to staging
2. **Phase 2:** Process staging files to enriched markdown

This is the recommended command for daily usage.

### Positional Arguments

#### `USERS...` (optional)
Specific usernames to sync. Leave empty for all users.

**Example:**
```bash
uv run trudy sync alice bob
```

### Options

Combines options from both `fetch` and `process` commands:

#### `--all` (default: true)
Sync all users.

#### `--user USERNAME`, `-u USERNAME` (repeatable)
Sync specific user.

**Example:**
```bash
uv run trudy sync --user alice
```

#### `--full`
Full sync - fetch all historical messages.

**Example:**
```bash
uv run trudy sync --full
```

#### `--limit INTEGER`
Limit number of messages to fetch per user.

**Example:**
```bash
uv run trudy sync --limit 100
```

#### `--skip-transcription`
Skip audio/video transcription.

**Example:**
```bash
uv run trudy sync --skip-transcription
```

#### `--skip-ocr`
Skip OCR text extraction.

**Example:**
```bash
uv run trudy sync --skip-ocr
```

#### `--skip-summarization`
Skip AI summarization.

**Example:**
```bash
uv run trudy sync --skip-summarization
```

#### `--skip-tags`
Skip automatic tag generation.

**Example:**
```bash
uv run trudy sync --skip-tags
```

#### `--workers INTEGER` (default: 3)
Number of parallel processing workers.

**Example:**
```bash
uv run trudy sync --workers 5
```

#### `--dry-run`
Preview what would be synced without writing files.

**Example:**
```bash
uv run trudy sync --dry-run
```

### Examples

#### Daily incremental sync (most common)
```bash
uv run trudy sync
```

#### Full historical sync (first time)
```bash
uv run trudy sync --full
```

#### Sync specific user
```bash
uv run trudy sync --user alice
```

#### Fast sync without AI features
```bash
uv run trudy sync --skip-transcription --skip-ocr --skip-summarization
```

#### Sync with verbose output
```bash
uv run trudy sync -v
```

#### Preview sync
```bash
uv run trudy sync --dry-run
```

### Output

Shows results from both phases:

```
Trudy 2.0 - Full Sync

Phase 1: Fetch

Fetch Results
┌──────────┬──────────┬──────────────────┐
│ User     │ Chat ID  │ Messages Fetched │
├──────────┼──────────┼──────────────────┤
│ alice    │ 12345678 │ 5                │
└──────────┴──────────┴──────────────────┘

Total: 1 users, 5 messages fetched

Phase 2: Process

Processing Report
...

✓ Sync complete!
```

### Exit Codes

- `0` - Success
- `1` - Error in either phase
- `130` - Interrupted by user (Ctrl+C)

---

## Exit Codes

All Trudy commands use standard exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success - command completed without errors |
| `1` | Error - command failed or encountered errors |
| `130` | Interrupted - user pressed Ctrl+C |

**Usage in scripts:**
```bash
#!/bin/bash
uv run trudy sync
if [ $? -eq 0 ]; then
    echo "Sync successful"
else
    echo "Sync failed"
    exit 1
fi
```

---

## Environment Variables

### `TELEGRAM_BOT_TOKEN`
**Required.** Your Telegram bot token from @BotFather.

**Example:**
```bash
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
uv run trudy sync
```

Or use `.env` file:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### `TRUDY_CONFIG`
Optional. Override default config file path.

**Example:**
```bash
export TRUDY_CONFIG="/path/to/config.yaml"
uv run trudy sync
```

---

## Common Workflows

### Daily Sync
```bash
# Run once a day
uv run trudy sync
```

### Fast Sync (No AI)
```bash
# For quick results
uv run trudy sync --skip-transcription --skip-ocr --skip-summarization
```

### Reprocess After Config Change
```bash
# Edit config/config.yaml
# Then:
uv run trudy process --reprocess
```

### Check What's Pending
```bash
# Dry run to see what would be processed
uv run trudy process --dry-run -v
```

### Full Historical Import
```bash
# First time setup
uv run trudy fetch --full
uv run trudy process
```

---

## Tips & Tricks

### Alias for Convenience
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
alias trudy="uv run trudy"
```

Then:
```bash
trudy sync  # Much shorter!
```

### Cron Job for Auto-Sync
```bash
# Edit crontab
crontab -e

# Add line to sync every hour
0 * * * * cd /path/to/trudy && uv run trudy sync --quiet
```

### Quick Status Check
```bash
# See what's in state
cat data/state.json | jq '.users | keys'
```

### Force Clean Restart
```bash
# Backup state
cp data/state.json data/state.json.backup

# Delete state
rm data/state.json

# Full sync will recreate everything
uv run trudy sync --full
```

---

## Getting Help

### Command Help
```bash
# General help
uv run trudy --help

# Command-specific help
uv run trudy fetch --help
uv run trudy process --help
uv run trudy sync --help
```

### Verbose Output
```bash
# See what's happening
uv run trudy -v sync
```

### Dry Run
```bash
# Preview without changes
uv run trudy --dry-run sync
```

---

**For more information:**
- [Quick Start Guide](QUICK_START.md) - Get started
- [Workflows Guide](WORKFLOWS.md) - Usage patterns
- [Configuration Guide](CONFIGURATION.md) - All settings
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Problem solving
