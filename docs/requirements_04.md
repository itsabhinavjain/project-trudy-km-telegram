# Trudy Refactoring Requirements & Implementation Plan

## Document Overview
This document outlines the complete refactoring plan for Trudy, transforming it from a single-phase processing system to a two-phase atomic workflow system with enhanced markdown formatting and improved CLI interface.

---

## Executive Summary

### Current System
- Single-phase processing: Fetch → Process → Save in one operation
- Combined workflows with multiple flags
- Basic markdown format
- Uses Click for CLI
- Manual + Auto-discovery modes

### New System
- **Two-phase processing**: Fetch → Staging | Staging → Process → Final
- **Atomic workflows**: Separate commands for discovery, fetching, and processing
- **Enhanced markdown**: Raw staging format + Rich post-processing format with metadata
- **Typer CLI**: Modern CLI with better UX
- **Auto-discovery only**: Remove manual configuration mode

---

## Core Changes

### Core Change 1: Two-Phase Architecture

#### Phase 1: Fetching
**Purpose**: Download messages from Telegram API and save to staging area

**Flow**:
1. Connect to Telegram API
2. Fetch new messages (incremental based on state)
3. Convert to raw markdown format
4. Save to staging directory
5. Update fetch state (tracking last_message_id per user)

**Storage Structure**:
```
data/
├── staging/
│   └── <username>/
│       ├── YYYY-MM-DD.md          # Raw messages for the day
│       └── media/                 # Downloaded media files
│           └── YYYY-MM-DD_HH-MM-SS_<type>.<ext>
└── processed/
    └── <username>/
        ├── YYYY-MM-DD.md          # Processed messages with metadata
        └── media/                 # Same media files (symlinks or references)
```

Abhinav : In the above storage structure, you can use the same media folder for both staging and processed. 

**Staging Markdown Format** (Simple, raw from API):
```markdown
## 14:30

Hello, this is a test message

---

## 14:35 - Image

![](media/2026-01-04_14-35-23_image.jpg)

Caption: My screenshot

---

## 14:40 - Video

[Video file](media/2026-01-04_14-40-15_video.mp4)

Caption: Important meeting recording

---

## 14:45 - Audio

[Audio file](media/2026-01-04_14-45-30_audio.ogg)

Voice message

---

## 14:50

Check out this article: https://example.com/article
```

Abhinav : The staging markdown file should be more simple here. In the header itself, add the verbatim text if available. 

#### Phase 2: Processing
**Purpose**: Process staged messages and generate enriched markdown

**Flow**:
1. Read messages from staging area
2. Detect unprocessed messages (using processing state)
3. Apply processors (transcription, OCR, summarization, link extraction)
4. Generate enriched markdown with metadata
5. Save to processed directory
6. Update processing state

**Processing State Tracking**:
- Track which messages from staging have been processed
- Store hash/checksum of staging file to detect changes
- Allow reprocessing if staging file changes

---

### Core Change 2: Atomic Workflows & CLI Commands

#### New CLI Structure (using Typer)

```bash
# 1. USER DISCOVERY
trudy discover [OPTIONS]
  --full              # Scan all historical messages for users
  --refresh           # Re-scan and update user list
  --format [json|table]  # Output format (default: table)
  -v, --verbose       # Verbose logging

# Output: Display discovered users in table format
# Action: Updates user state in state.json

# 2. MESSAGE FETCHING
trudy fetch [OPTIONS] [USERS...]
  --all               # Fetch for all discovered users (default)
  --user <username>   # Fetch for specific user(s), repeatable
  --full              # Full sync (all history), default: incremental
  --limit <n>         # Limit number of messages to fetch
  --dry-run           # Preview what would be fetched
  -v, --verbose       # Verbose logging

# Output: Raw messages saved to staging area
# Action: Downloads messages and media to staging/

# 3. MESSAGE PROCESSING
trudy process [OPTIONS] [USERS...]
  --all               # Process all users (default)
  --user <username>   # Process specific user(s), repeatable
  --date <YYYY-MM-DD> # Process specific date only
  --skip-transcription  # Skip audio/video transcription
  --skip-ocr          # Skip image OCR
  --skip-summarization  # Skip AI summarization
  --skip-tags         # Skip automatic tag generation
  --reprocess         # Reprocess already processed messages
  --workers <n>       # Number of parallel workers (default: 3)
  --dry-run           # Preview what would be processed
  -v, --verbose       # Verbose logging

# Output: Enriched messages saved to processed area
# Action: Processes staging files and saves to processed/

# 4. COMBINED WORKFLOW (Convenience)
trudy sync [OPTIONS] [USERS...]
  # Equivalent to: trudy fetch + trudy process
  # Accepts combined options from both commands
  --all               # Sync all users
  --user <username>   # Sync specific user(s)
  --full              # Full sync (all history)
  --skip-summarization  # Skip summarization
  -v, --verbose       # Verbose logging

# 5. STATUS & INFORMATION
trudy status [OPTIONS]
  --user <username>   # Show status for specific user
  --format [json|table]  # Output format

# Output: Shows sync status, message counts, last sync times

trudy info
  # Show configuration, model status, system info

# 6. UTILITIES
trudy clean [OPTIONS]
  --staging           # Clean staging area
  --processed         # Clean processed area (dangerous!)
  --user <username>   # Clean specific user's data
  --before <YYYY-MM-DD>  # Clean data before date
  --dry-run           # Preview what would be deleted

trudy migrate
  # Migrate from old single-phase format to new two-phase format
```

#### Example Workflows

**Daily incremental sync**:
```bash
trudy sync
```

**Discover new users and fetch their messages**:
```bash
trudy discover
trudy fetch --all
trudy process --all
```

**Fetch without processing (useful for batch operations)**:
```bash
trudy fetch --all --full
# Later, process in batches with different options
trudy process --user alice --skip-summarization
trudy process --user bob
```

**Reprocess messages with new AI models**:
```bash
trudy process --all --reprocess
```

**Fetch specific user with limit**:
```bash
trudy fetch --user alice --limit 100
trudy process --user alice
```

---

### Core Change 3: Enhanced Markdown Formats

#### Post-Processing Markdown Format

**Proposed Enhanced Format** (YAML-style metadata blocks):

```markdown
## 14:30
type: text
content: |
  Hello, this is a test message with a link: https://example.com/article
links:
  - url: https://example.com/article
    title: "Example Article Title"
    type: article
tags:
  - #communication
  - #example

---

## 14:35 - Image
type: image
file: ![[2026-01-04_14-35-23_screenshot.jpg]]
about: Screenshot of error message
ocr_text: |
  Error: Connection timeout
  Please check your network settings
tags:
  - #screenshot
  - #error
  - #troubleshooting

---

## 14:40 - Video
type: video
file: ![[2026-01-04_14-40-15_meeting.mp4]]
duration: 15:32
summary: |
  - Discussed Q1 roadmap
  - Review of customer feedback
  - Action items for next sprint
transcript: ![[2026-01-04_14-40-15_meeting_transcript.txt]]
tags:
  - #meeting
  - #planning
  - #video

---

## 14:45 - Audio
type: voice_message
file: ![[2026-01-04_14-45-30_voice.ogg]]
duration: 00:45
summary: Reminder to review the PR before end of day
transcript: ![[2026-01-04_14-45-30_voice_transcript.txt]]
tags:
  - #reminder
  - #audio

---

## 14:50 - YouTube Video
type: youtube
url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
title: "Rick Astley - Never Gonna Give You Up"
channel: "Rick Astley"
duration: 03:33
summary: |
  - Classic 80s pop music video
  - Iconic dance moves and fashion
  - Cultural phenomenon and internet meme
transcript: ![[2026-01-04_14-50-00_youtube_transcript.txt]]
tags:
  - #music
  - #youtube
  - #80s

---

## 14:55 - Document
type: document
file: ![[2026-01-04_14-55-12_report.pdf]]
filename: "Q4_Financial_Report.pdf"
size: 2.4 MB
tags:
  - #document
  - #finance

---

## 15:00 - Video Note
type: video_note
file: ![[2026-01-04_15-00-20_note.mp4]]
duration: 00:30
summary: Quick demo of new feature
transcript: ![[2026-01-04_15-00-20_note_transcript.txt]]
tags:
  - #demo
  - #feature

---
```


Abhinav : I agree with the above format. Make sure that you are adding verbatim message in the headers so that it is easy to track. Additionally make the staging area markdown very simple. 


**Key Metadata Fields by Type**:

| Message Type | Required Fields | Optional Fields |
|--------------|----------------|-----------------|
| text | type, content | links, tags |
| image | type, file | about, ocr_text, tags |
| photo | type, file | about, ocr_text, tags |
| video | type, file, duration | summary, transcript, tags |
| video_note | type, file, duration | summary, transcript, tags |
| audio | type, file, duration | summary, transcript, tags |
| voice | type, file, duration | summary, transcript, tags |
| youtube | type, url, title | channel, duration, summary, transcript, tags |
| document | type, file, filename | size, tags |

---

### Core Change 4: Remove Manual User Configuration

**Changes**:
- Remove `users` section from config.yaml
- Remove manual user configuration logic
- Keep only auto-discovery workflow
- Simplify state management

**Migration**:
- For existing manual configurations, run `trudy discover` to convert to auto-discovery

---

### Core Change 5: Switch to Typer CLI

**Benefits of Typer**:
- Better type hints and validation
- Automatic help generation
- Subcommands support (discover, fetch, process, sync)
- Rich integration for beautiful output
- Better error messages

**Dependencies**:
- Replace `click` with `typer[all]`
- Add `rich` for enhanced terminal output (already used)

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)
1. **Update dependencies**
   - Add typer[all] to pyproject.toml
   - Remove click dependency
   - Test installation

2. **Create new storage structure**
   - Add staging/ and processed/ directories
   - Update StorageConfig in src/core/config.py
   - Create migration utility for existing data

3. **Extend state management**
   - Add fetch_state (last_message_id per user for fetching)
   - Add process_state (last processed timestamp per user/date)
   - Add file checksums for change detection

### Phase 2: Fetching Layer (Days 3-4)
1. **Create staging writer**
   - New src/markdown/staging_writer.py
   - Implement simple markdown format
   - Media downloads to staging/

2. **Refactor MessageFetcher**
   - Separate concerns: fetch only, no processing
   - Save to staging area instead of direct processing
   - Update state management for fetch tracking

3. **Implement discover command**
   - Create src/cli/discover.py
   - User discovery and listing
   - JSON/table output formats

4. **Implement fetch command**
   - Create src/cli/fetch.py
   - Incremental and full sync modes
   - User filtering

### Phase 3: Processing Layer (Days 5-7)
1. **Create staging reader**
   - New src/markdown/staging_reader.py
   - Parse staging markdown files
   - Detect unprocessed messages

2. **Create enhanced markdown formatter**
   - New src/markdown/processed_formatter.py
   - Implement metadata block format
   - Support all message types

3. **Refactor processors**
   - Update processors to work with staging input
   - Add metadata generation
   - Implement automatic tagging

4. **Implement process command**
   - Create src/cli/process.py
   - Selective processing options
   - Reprocessing support
   - Parallel processing with workers

### Phase 4: CLI & Commands (Days 8-9)
1. **Implement Typer CLI**
   - Create src/cli/main.py with Typer app
   - Implement all commands (discover, fetch, process, sync, status, info, clean)
   - Rich output formatting

2. **Add sync command**
   - Combined fetch + process workflow
   - Option inheritance

3. **Add utility commands**
   - status: Show sync state
   - info: System information
   - clean: Data cleanup utilities

### Phase 5: Features & Polish (Days 10-12)
1. **Implement automatic tagging**
   - Rule-based tags (file types, patterns)
   - AI-based tags (optional)
   - Tag configuration

2. **Implement OCR for images**
   - Add OCR processor (pytesseract or cloud OCR)
   - Configuration options
   - Error handling

3. **Add migration utility**
   - Convert old data to new structure
   - Preserve existing processed messages
   - Validation

4. **Update documentation**
   - Update README.md
   - Update CLAUDE.md
   - Add migration guide

### Phase 6: Testing & Validation (Days 13-14)
1. **Write tests**
   - Unit tests for new components
   - Integration tests for commands
   - E2E workflow tests

2. **Manual testing**
   - Test all CLI commands
   - Test edge cases
   - Performance testing

3. **Bug fixes and refinement**

---

## Data Structure Changes

### State File Structure (state.json)

```json
{
  "version": "2.0",
  "users": {
    "alice": {
      "chat_id": 123456789,
      "phone": "+1234567890",
      "first_seen": "2026-01-01T10:00:00Z",
      "last_seen": "2026-01-04T15:30:00Z",
      "fetch_state": {
        "last_message_id": 1234,
        "last_fetch_time": "2026-01-04T15:30:00Z",
        "total_messages_fetched": 500
      },
      "process_state": {
        "last_processed_date": "2026-01-04",
        "last_process_time": "2026-01-04T15:45:00Z",
        "total_messages_processed": 498,
        "pending_files": [
          "staging/alice/2026-01-04.md"
        ]
      }
    }
  },
  "statistics": {
    "total_users": 5,
    "total_fetched": 2500,
    "total_processed": 2450,
    "total_media": 800,
    "total_transcriptions": 120,
    "total_summaries": 300
  }
}
```

### Configuration Changes (config.yaml)

```yaml
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  api_url: "https://api.telegram.org"
  timeout: 30
  retry_attempts: 3

# Users section removed - auto-discovery only

storage:
  base_dir: "./data"
  staging_dir: "staging"      # NEW
  processed_dir: "processed"  # NEW
  notes_subdir: "notes"       # DEPRECATED (kept for migration)
  media_subdir: "media"

transcription:
  enabled: true
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "whisper"
    timeout: 300
  youtube_prefer_transcript: true

summarization:
  enabled: true
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama2"
    temperature: 0.7
    max_tokens: 500
  claude:
    cli_path: "claude"
    model: "claude-sonnet-4-5"
    max_tokens: 1000
  prompts:
    video_summary: "Summarize the key points from this video transcript in 3-5 bullet points."
    audio_summary: "Summarize the main topics discussed in this audio recording."
    article_summary: "Provide a concise summary of this article in 2-3 paragraphs."
    youtube_summary: "Summarize this YouTube video, highlighting key takeaways."

processing:
  max_workers: 3               # Renamed from max_concurrent
  skip_errors: true
  retry_failed: true
  ocr:                         # NEW
    enabled: true
    provider: "tesseract"      # Options: tesseract, cloud
    languages: ["eng"]
  tagging:                     # NEW
    enabled: true
    auto_rules:
      - pattern: "screenshot"
        tag: "#screenshot"
      - pattern: "meeting"
        tag: "#meeting"
    ai_tagging: false          # Use AI to generate tags

markdown:
  staging_format: "simple"     # NEW: simple, detailed
  processed_format: "enhanced" # NEW: basic, enhanced
  timezone: "UTC"
  timestamp_format: "HH:MM"
  include_message_id: false
  wikilink_style: "obsidian"

logging:
  level: "INFO"
  file: "./logs/trudy.log"
  error_file: "./logs/errors.log"
  max_bytes: 10485760
  backup_count: 5
```

---

## Clarifying Questions

### 1. Staging Area Management
**Question**: Should the staging area be:
- **Option A**: Persistent (never deleted automatically)
- **Option B**: Temporary (cleared after successful processing)
- **Option C**: Configurable retention (e.g., keep for 7 days)

**Recommendation**: Option C with configurable retention for debugging and reprocessing needs.
Abhinav : I agree with the above recommendation.


### 2. Reprocessing Strategy
**Question**: When reprocessing messages, should we:
- **Option A**: Only reprocess if staging file changed (checksum-based)
- **Option B**: Always reprocess when --reprocess flag is used
- **Option C**: Prompt user to confirm reprocessing

**Recommendation**: Option A by default, Option B with --reprocess flag, skip prompts (automation-friendly).
Abhinav : I agree with the above recommendation.

### 3. Media File Handling
**Question**: For media files in processed area, should we:
- **Option A**: Create symlinks to staging media files
- **Option B**: Copy media files from staging to processed
- **Option C**: Keep only in staging, reference from processed markdown

**Recommendation**: Option C to avoid duplication, use relative paths in markdown.
Abhinav : Create in a separate folder called media. staging and processed area should have only the markdown files. The media files should be stored in the common media folder.

### 4. Post-Processing Markdown Format
**Question**: For the enhanced markdown format, should we use:
- **Option A**: YAML frontmatter (standard, parseable)
  ```markdown
  ---
  type: image
  file: ...
  tags: [...]
  ---
  Content here
  ```
- **Option B**: Indented YAML blocks (as shown in requirements)
  ```markdown
  ## 14:30
  type: image
  file: ...
  tags:
    - #tag1
  ```
- **Option C**: JSON blocks
- **Option D**: Custom format optimized for Obsidian readability

**Recommendation**: Option B for better readability in Obsidian preview mode, easier to edit manually.
Abhinav : I agree with the above recommendation.

### 5. Automatic Tagging Strategy
**Question**: How should automatic tags be generated?
- **Option A**: Rule-based only (patterns, file types, keywords)
- **Option B**: AI-based only (using LLM to generate relevant tags)
- **Option C**: Hybrid (rules + AI, configurable)

**Recommendation**: Option C - rules for common patterns (fast), AI for content analysis (optional).
Abhinav : I agree with the above recommendation.

### 6. Backward Compatibility
**Question**: Should we maintain backward compatibility with old data structure?
- **Option A**: Yes, read old format and migrate on-the-fly
- **Option B**: No, require explicit migration command
- **Option C**: Read-only compatibility (can read old, but write new)

**Recommendation**: Option B with a comprehensive migration command (`trudy migrate`).
Abhinav : You dont need to maintain any backward compatibility. Infact you can delete the old data structure. We also dont need to migrate the current data. Consider this as a fresh repo. 

### 7. Processing State Granularity
**Question**: Should processing state track:
- **Option A**: Per-file (each staging markdown file)
- **Option B**: Per-message (individual message IDs)
- **Option C**: Per-day (processed dates only)

**Recommendation**: Option A - per-file tracking with checksums, good balance of granularity and performance.
Abhinav : Explain this again. 

### 8. Error Handling in Two-Phase System
**Question**: If processing fails for a message, should we:
- **Option A**: Leave in staging, retry on next process run
- **Option B**: Move to processed with error marker
- **Option C**: Move to separate error directory

**Recommendation**: Option A - keep in staging with error tracking in state, allow reprocessing.
Abhinav : I agree with the above recommendation.

### 9. YouTube Transcript Format
**Question**: Should YouTube transcripts be:
- **Option A**: Saved as separate .txt files (like video transcripts)
- **Option B**: Embedded in markdown with timestamps
- **Option C**: Both (file + summary in markdown)

**Recommendation**: Option C - full transcript in file for reference, timestamped summary in markdown for readability.
Abhinav : I agree with the above recommendation.

### 10. CLI Command Grouping
**Question**: Should we organize commands as:
- **Option A**: Flat structure (trudy fetch, trudy process, etc.)
- **Option B**: Grouped subcommands (trudy sync fetch, trudy sync process, trudy user discover, etc.)
- **Option C**: Hybrid (common commands flat, utilities grouped)

**Recommendation**: Option A - flat structure is simpler and more intuitive for daily use.
Abhinav : I agree with the above recommendation.

---

## Migration Strategy
Abhinav : This is not required. We have not run Trudy yet. We dont need to implement any migration strategy. Dont include any migration code. 

### For Existing Users

**Migration Command**: `trudy migrate`

**Steps**:
1. Analyze current data structure (data/users/)
2. Create new directory structure (staging/, processed/)
3. Convert existing processed messages to new format
4. Preserve media files
5. Update state.json to new format
6. Create backup of old structure
7. Validate migration

**Example**:
```bash
# Backup current data
trudy migrate --backup

# Dry run to preview changes
trudy migrate --dry-run

# Execute migration
trudy migrate

# Verify migration
trudy status --format json
```

### Post-Migration Workflow
Abhinav : This is not required. We have not run Trudy yet. We dont need to implement any migration strategy. Dont include any migration code. 

**Old Workflow**:
```bash
uv run trudy              # Fetch and process
uv run trudy --full       # Full sync
```

**New Workflow**:
```bash
trudy sync                # Fetch and process (equivalent)
trudy sync --full         # Full sync
```

**Or separate steps**:
```bash
trudy fetch               # Just fetch to staging
trudy process             # Process staged messages
```

---

## Success Criteria

- [ ] All CLI commands working as specified
- [ ] Two-phase architecture fully functional
- [ ] Staging and processed directories properly maintained
- [ ] State management tracks both fetch and process states
- [ ] Enhanced markdown format includes all metadata
- [ ] Automatic tagging implemented (at least rule-based)
- [ ] OCR for images working
- [ ] Migration utility converts old data successfully
- [ ] All existing features preserved (transcription, summarization, etc.)
- [ ] Tests passing (unit + integration)
- [ ] Documentation updated
- [ ] Performance acceptable (no significant degradation)

---

## Risk Assessment


### High Risk
- **State management complexity**: Two separate states (fetch + process) could lead to sync issues
  - Mitigation: Comprehensive state validation and recovery mechanisms

- **Data migration**: Risk of data loss during migration from old to new structure
  - Mitigation: Mandatory backup step, validation checks, rollback capability
Abhinav : Dont worry about data migration. Please give suggestion on state management and how it should be handled. Should we have two different state files? 


### Medium Risk
- **Markdown format parsing**: Complex YAML-style format could be fragile
  - Mitigation: Robust parsing with error handling, validation

- **Performance**: Two-phase processing could be slower than current single-phase
  - Mitigation: Optimize I/O, parallel processing, incremental processing

### Low Risk
- **CLI UX**: Users need to learn new commands
  - Mitigation: Comprehensive documentation, backward-compatible sync command
Abhinav : Dont worry about this. Users will learn new commands till the time there is proper documentation of the tool. 

---

## Questions for User

Before proceeding with implementation, please clarify:

1. **Staging retention policy** - How long should we keep staging files? (Options A/B/C above)
Abhinav : Answered above 

2. **Markdown format preference** - Do you prefer YAML frontmatter, indented YAML blocks, or another format for post-processing markdown? (See question 4 above)
Abhinav : Answered above 

3. **Media file handling** - Should media files be symlinked, copied, or referenced from staging? (See question 3 above)
Abhinav : Answered above 

4. **Automatic tagging** - Do you want rule-based, AI-based, or hybrid tagging? Any specific tags or patterns you'd like to auto-generate?
Abhinav : Answered above 

5. **OCR requirements** - Which OCR provider should we use? Tesseract (local, free) or cloud OCR (better quality, costs money)?
Abhinav : Please use Tesseract. Also givem an opton to use cloud OCR. This we should be able to specify in config. 

6. **Processing triggers** - Should processing happen automatically after fetching, or only on explicit command?
Abhinav : After explicit command 

7. **Additional metadata** - Any other metadata fields you'd like in the processed markdown format beyond what's specified?
Abhinav : This looks good to me. Do you suggest any additional metadata fields?

8. **Link extraction** - For text messages with links, should we fetch article titles, descriptions, OpenGraph data, or just keep URLs as-is?
Abhinav : Yes, please do link extraction. Please make changes to the output markdown structure accordingly.

9.  **Timezone handling** - Should timestamps in markdown use UTC or local timezone? Should we store both?
Abhinav : Use local timezone. 

10. **Notification/reporting** - After sync/process, should we generate summary reports (e.g., "Processed 50 messages, 10 videos transcribed, 5 articles summarized")?
Abhinav : Yes please. 

---

Abhinav : Make sure that you are also giving me a plan to update the various documentation. 


## Next Steps

Once you answer the clarifying questions above, I will:

1. Update this requirements document with your preferences
2. Create detailed technical specifications for each component
3. Begin implementation following the phased plan
4. Provide regular progress updates

Please review this document and provide your feedback and answers to the questions.
