# Changelog

All notable changes to Trudy will be documented in this file.

## [2.0.0] - 2026-01-05

### 🎉 Major Rewrite

Complete rewrite of Trudy with modern architecture and enhanced features.

### Added

#### Architecture
- **Two-Phase Processing**: Separate fetch and process stages for atomic operations
- **Dual-State Management**: Track fetch_state and process_state independently
- **Checksum-Based Reprocessing**: SHA-256 checksums to detect file changes
- **Separate Storage Directories**: staging/, processed/, and shared media/

#### CLI (Typer Framework)
- `discover` - Discover users who have messaged the bot
- `fetch` - Fetch messages from Telegram to staging area
- `process` - Process staging files to enriched markdown
- `sync` - Combined fetch + process workflow (most common)
- `status` - Show sync status for all users
- `info` - Show system information and configuration
- `clean` - Clean staging/processed/media areas with retention policies

#### Features
- **OCR Support**: Extract text from images using Tesseract or cloud providers
- **Auto-Tagging**: Rule-based and AI-powered tag generation
- **Link Metadata Extraction**: Automatic title and description from URLs
- **Context Tracking**: Preserve reply, forward, and edit context
- **Rich Metadata**: YAML frontmatter with comprehensive message data
- **Progress Reporting**: Real-time progress bars and statistics
- **Dry-Run Mode**: Preview operations before executing

#### AI Enhancements
- OCR text extraction from images (Tesseract, Google Vision, Azure, AWS)
- Auto-tagging with configurable rules and optional AI
- Enhanced link processing with metadata extraction

### Changed

- **CLI Framework**: Migrated from Click to Typer for better UX
- **Output Format**: Added rich console output with tables and colors
- **Markdown Format**: Split into simple staging and rich processed formats
- **State Structure**: Enhanced with checksums, pending files, and timestamps
- **Configuration**: Expanded with OCR, tagging, and link extraction sections
- **Media Storage**: Moved to shared directory instead of per-user

### Improved

- **Error Handling**: Graceful failures with detailed error messages
- **Performance**: Checksum-based skipping of unchanged files
- **Logging**: Enhanced structured logging with Rich integration
- **Documentation**: Comprehensive guides for all features
- **Testing**: 65 automated tests with 75% coverage
- **Help System**: Auto-generated from command docstrings

### Breaking Changes

⚠️ **No backward compatibility with v1.x**

- Data structure completely changed (staging + processed vs notes)
- State file format enhanced (dual-state tracking)
- Configuration format updated (new sections)
- CLI commands completely different
- Media storage location changed

**Migration**: Fresh start required. Export v1.x data before upgrading.

### Technical Details

#### Dependencies Added
- `typer>=0.9.0` - Modern CLI framework
- `rich>=13.0.0` - Beautiful console output
- `pytesseract>=0.3.10` - OCR support
- Cloud OCR providers (optional)

#### Dependencies Removed
- `click` - Replaced by Typer

#### New Files Created
- `src/cli/` - All CLI command modules
- `src/markdown/staging_writer.py` - Simple staging format
- `src/markdown/staging_reader.py` - Parse staging files
- `src/markdown/processed_writer.py` - Rich processed format
- `src/ai/ocr.py` - OCR integration
- `src/ai/tagger.py` - Auto-tagging
- `src/utils/checksum.py` - Checksum utilities
- `src/core/processor.py` - Processing orchestration

#### Files Modified
- `src/core/state.py` - Dual-state management
- `src/core/config.py` - Enhanced configuration
- `src/telegram/fetcher.py` - Fetch-only refactor
- `src/processors/*.py` - Updated for staging input
- `pyproject.toml` - Dependencies and entry point

### Performance

- Fetch: ~100 messages/minute (API limited)
- Process (with AI): ~20 messages/minute
- Process (without AI): ~500 messages/minute
- Reprocess (unchanged): ~1000 messages/minute (skipped)

### Documentation

New comprehensive documentation:
- `docs/QUICK_START.md` - 5-minute setup guide
- `docs/CLI_REFERENCE.md` - Complete CLI reference
- `docs/WORKFLOWS.md` - Common usage patterns
- `docs/IMPLEMENTATION_COMPLETE.md` - Implementation summary
- Updated `docs/README.md` - Main user guide
- Updated `CLAUDE.md` - Developer guide

### Testing

- **65 tests** across all components
- **75% overall coverage**
- Unit tests for utilities and core components
- CLI command tests
- Integration workflow tests

### Known Issues

- Some integration tests need API refinement
- Parallel processing workers not fully implemented
- Cloud OCR providers are placeholders (Tesseract works)

---

## [1.x] - Previous Version

Legacy single-phase architecture with Click CLI.

See git history for v1.x changes.

---

## Version Numbering

Trudy follows [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality
- PATCH version for backwards-compatible bug fixes

**2.0.0** represents a major breaking change with complete rewrite.
