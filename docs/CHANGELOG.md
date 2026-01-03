# Changelog

## [Unreleased] - Auto-Discovery Feature

### Added
- **Automatic User Discovery**: The system now automatically discovers users who message the bot
  - No need to manually configure chat IDs in config.yaml
  - Usernames are intelligently generated from Telegram username, name, or user ID
  - Supports unlimited users without configuration
  - `users: []` in config.yaml enables auto-discovery mode (now the default)
  - **Continuous Discovery**: Users are discovered and accumulated across all runs
    - Day 1: 3 users message → 3 users tracked in state
    - Day 2: 4 new users + 1 old user message → All 7 users tracked
    - System maintains complete history of all users who have ever interacted with the bot

- **User Discovery Command**: New `--discover-users` CLI flag
  - Run `uv run trudy --discover-users` to list all users without processing messages
  - Shows user statistics including total messages, first message time, and last fetch time
  - Useful for auditing and managing discovered users

### Changed
- **Configuration**: The `users` section in `config/config.yaml` is now optional
  - Defaults to empty list `[]` for auto-discovery
  - Can still be manually configured for custom usernames
  - Backward compatible with existing configurations

- **Message Fetching**: Enhanced fetcher with new `fetch_and_discover_users()` method
  - Automatically detects all users from bot messages
  - Creates UserConfig dynamically with generated usernames
  - Handles username conflicts intelligently

- **CLI Output**: Improved status messages
  - Shows "Auto-discovering users..." when in discovery mode
  - Shows "Using configured users..." when manually configured
  - Displays discovered users with their chat IDs

### Implementation Details

**Files Modified:**
1. `src/core/config.py`
   - Made `users` field optional with empty list default
   - Updated validation to handle empty users list

2. `src/telegram/fetcher.py`
   - Added `generate_username_from_telegram()` helper function
   - Added `fetch_and_discover_users()` method for auto-discovery
   - Intelligent username generation with conflict resolution
   - **Updated for continuous discovery**: Method now loads existing users from state.json
   - Merges previously discovered users with newly discovered users
   - Returns complete list of all users (existing + new)

3. `src/main.py`
   - Added auto-discovery mode detection
   - Separate code paths for auto-discovery vs manual configuration
   - Maintains backward compatibility
   - **New `--discover-users` CLI flag**: List all discovered users without processing messages
   - Displays user statistics and updates state for newly discovered users

4. `config/config.yaml`
   - Updated with comprehensive documentation
   - Set default to `users: []` for auto-discovery
   - Included examples for both modes

5. `README.md`
   - Simplified setup instructions
   - Removed manual chat ID configuration steps
   - Added note about auto-discovery

6. `USAGE.md`
   - Added "User Discovery Modes" section
   - Detailed explanation of auto-discovery
   - Examples of username generation
   - Comparison of auto vs manual modes

7. `requirements.md`
   - Added FR-2.1.4 for automatic user discovery
   - Documented both modes

### Username Generation Priority

When discovering users automatically:

1. **Telegram @username** (if available)
   - Example: `@john_doe` → `john_doe`

2. **First name + Last name** (if no username)
   - Example: "John Doe" → `john_doe`
   - Spaces replaced with underscores
   - Special characters removed

3. **User ID fallback** (if no name available)
   - Example: User ID 123456789 → `user_123456789`

4. **Conflict resolution** (if username already exists)
   - Example: `john_doe` → `john_doe_1`, `john_doe_2`, etc.

### Migration Guide

**For New Users:**
Simply use the default configuration with `users: []` - no action needed!

**For Existing Users with Manual Configuration:**
You have two options:

1. **Keep manual configuration** (no changes needed)
   - Your existing `config.yaml` will continue to work
   - Users will be processed as before

2. **Switch to auto-discovery** (optional)
   - Change `users: [...]` to `users: []` in config.yaml
   - Run `uv run trudy --full` to rediscover users
   - Usernames may change based on Telegram info
   - Update folder references if needed

### Benefits

✅ **Simpler Setup**: No need to find and configure chat IDs
✅ **Dynamic**: Automatically handles new users
✅ **Scalable**: Works with any number of users
✅ **Intelligent**: Generates meaningful usernames
✅ **Flexible**: Still supports manual configuration when needed
✅ **Backward Compatible**: Existing configurations work as-is

### Example Usage

```bash
# With auto-discovery (default)
uv run trudy

# Output:
# Auto-discovering users from bot messages...
# Discovered new user: john_doe (chat_id: 123456789)
# Total users: 3, New messages: 15
```

```bash
# Discover and list all users
uv run trudy --discover-users

# Output:
# Discovering all users...
#
# Discovered 7 users:
#
#   • john_doe
#     Chat ID: 123456789
#     Total messages: 42
#     First message: 2026-01-01 10:00:00
#     Last fetch: 2026-01-03 18:30:00
#
#   • jane_smith
#     Chat ID: 987654321
#     Total messages: 28
#     First message: 2026-01-02 14:22:00
#     Last fetch: 2026-01-03 18:30:00
#   ...
```

```bash
# With manual configuration
uv run trudy

# Output:
# Using configured users...
# Fetching messages...
# Found 10 new messages
```
