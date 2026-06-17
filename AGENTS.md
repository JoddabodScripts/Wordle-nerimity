# Wordle Bot for Nerimity - AI Agent Reference

*Generated on 2026-06-17 by init skill*

## Quick Overview

A feature-rich Wordle bot for the Nerimity chat platform with XP progression (100 levels), daily/event-based word puzzles, leaderboards, hard mode, hints, duels, streak tracking, and automated reminders. Built with Python 3.9+ and the Nerimity SDK.

## Project Type & Stack

- **Language:** Python 3.9+
- **Framework:** nerimity-sdk (async event-driven bot framework)
- **Package Manager:** pip
- **Runtime:** Async/await with asyncio
- **Data Storage:** JSON files in `data/` directory
- **Environment:** dotenv for configuration

## Directory Structure

```
wordle/
├── src_py/                      # All Python source code
│   ├── bot.py                   # Main entry point, command handlers, event listeners
│   ├── game_logic.py            # Core Wordle mechanics, guess evaluation, board rendering
│   ├── game_state_store.py      # Game state persistence (JSON)
│   ├── game_scoring.py          # XP calculation, hint penalties, effective guess counts
│   ├── leaderboard_store.py     # Daily/event leaderboard management
│   ├── leaderboard_notifier.py  # Auto-notification system for leaderboard updates
│   ├── leaderboard_message_store.py  # Track leaderboard message IDs for editing
│   ├── stats.py                 # User stats, XP system, level progression, all-time leaderboards
│   ├── xp_store.py              # Comeback bonus tracking (2x XP after 7+ days away)
│   ├── word_list.py             # Word pools for daily and all event modes
│   ├── events.py                # Event definitions (Undertale, Deltarune, Genshin, Forsaken, Vocaloid)
│   ├── duel_store.py            # 1v1 turn-based duel mode logic
│   ├── genshin_countdown.py     # Genshin Impact event date calculator
│   ├── forsaken_store.py        # Forsaken event date tracking
│   ├── streak_reaction_store.py # Emoji reactions for streak milestones
│   ├── reaction_messages.py     # Message reaction system
│   ├── dm_channel_store.py      # DM channel ID persistence
│   ├── debug_store.py           # Owner-only debug mode and command locking
│   └── max_level_store.py       # Level 100 achievement notification tracking
├── data/                        # Runtime JSON data (generated, gitignored)
│   ├── game-state.json          # Active and completed games
│   ├── leaderboard-YYYY-MM-DD.json   # Daily leaderboards
│   ├── leaderboard-YYYY-MM-DD-eventkey.json  # Event leaderboards
│   ├── genshin-countdown.json   # Genshin event scheduling
│   └── ...                      # Other runtime state files
├── .env                         # Environment variables (not in git)
├── .env.example.py              # Environment template
├── requirements.txt             # Python dependencies
├── README.md                    # User-facing documentation
├── CONTRIBUTING.md              # Developer guidelines
└── LICENSE                      # License file
```

## Entry Points

- **Main:** `src_py/bot.py` - Run with `python src_py/bot.py`
- **Entry function:** `bot.run()` at end of bot.py starts the event loop
- **Environment:** Requires `.env` file with `NERIMITY_TOKEN`, `OWNER_USER_ID`, `REMINDER_CHANNEL_ID`, `REMINDER_CRON`

## Key Files & Directories

### Core Game Logic
- `src_py/game_logic.py` - Game state management, guess evaluation, hint system, board rendering (text and HTML), hard mode validation, give-up functionality
- `src_py/game_state_store.py` - JSON persistence layer for active games (uses `data/game-state.json`)
- `src_py/game_scoring.py` - XP calculation with multipliers (hard mode, streaks, comeback bonus), hint penalty system
- `src_py/word_list.py` - Word pools: WORDS (500+ daily words), GENSHIN (character aliases), UNDERTALE, DELTARUNE, FORSAKEN, VOCALOID

### Statistics & Progression
- `src_py/stats.py` - XP system (100 levels), level names/tiers, all-time leaderboards, user stats aggregation, streak tracking
- `src_py/xp_store.py` - Comeback bonus (2x XP after 7+ days inactive), last-played tracking
- `src_py/leaderboard_store.py` - Daily and event-specific leaderboards, result recording, file cleanup
- `src_py/leaderboard_notifier.py` - Auto-updates leaderboard messages when new completions occur

### Events & Special Modes
- `src_py/events.py` - Event definitions with keys, titles, dates (fixed or dynamic)
- `src_py/genshin_countdown.py` - Calculates Genshin Impact update dates (42-day cycle)
- `src_py/forsaken_store.py` - Manual date tracking for Forsaken event
- `src_py/duel_store.py` - Turn-based 1v1 mode (no XP, separate from daily games)

### Bot Infrastructure
- `src_py/bot.py` - Command handlers for 20+ commands, event listeners, message formatting, reaction handling, cron reminders
- `src_py/debug_store.py` - Owner-only debug mode to lock/unlock commands
- `src_py/dm_channel_store.py` - Persistent DM channel IDs for user notifications
- `src_py/streak_reaction_store.py` - Emoji reactions for streak milestones (3, 5, 10, etc.)
- `src_py/reaction_messages.py` - Message reaction persistence
- `src_py/max_level_store.py` - Tracks which users have been notified of hitting level 100

### Data Directory
- `data/` - Runtime JSON files, created automatically, not in git
- Leaderboard files follow pattern: `leaderboard-YYYY-MM-DD[-eventkey].json`
- Game state consolidated in `game-state.json` with structure: `{"games": {...}, "currentStateByUser": {...}}`

## Architecture

**Event-driven async bot architecture:**
- Main loop in `bot.py` listens for Nerimity events (messages, button clicks, reactions)
- Commands trigger game logic functions that manipulate in-memory state
- State is persisted to JSON files via store modules
- Leaderboards auto-update via notifier when games complete
- Cron scheduler sends daily reminders

**Data flow:**
1. User sends `/wordle` → bot.py handler → game_logic.start_or_get_game() → game_state_store loads/saves JSON
2. User sends `/answer CRANE` → bot.py handler → game_logic.make_guess() → evaluates guess → updates state → records result in leaderboard_store
3. Game completes → leaderboard_notifier.notify() → edits existing leaderboard messages with updated rankings

**Key patterns:**
- Store modules encapsulate JSON I/O (load on import, save on mutation)
- Game state uses composite keys: `{user_id}:{date_key}:{event_key}:{run_id}`
- User has "current state" pointer to track active game context
- Events resolved dynamically: check date → match to event definition → use event word pool

## Dependencies

### Production
- `nerimity-sdk[cron]` - Nerimity bot framework with cron scheduling
- `python-dotenv` - Environment variable management
- `aiohttp` - Async HTTP client (SDK dependency)

### Development
- `pytest>=7.0.0` - Test framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-mock>=3.10.0` - Mocking utilities

**Note:** No Node.js dependencies despite `package.json` reference in README (likely outdated docs)

## Code Conventions

### Python Style
- **PEP 8** compliance (4 spaces, snake_case functions, PascalCase classes)
- **Type hints** used extensively: `def func(arg: str) -> dict:`
- **Docstrings** for public functions (module-level docstrings present)
- **Private functions** prefixed with underscore: `_persist()`, `_get_date_key()`

### Naming
- **Functions/variables:** `snake_case` (`make_guess`, `user_id`, `date_key`)
- **Classes:** `PascalCase` (minimal class usage, mostly functional)
- **Constants:** `UPPER_SNAKE_CASE` (`MAX_GUESSES`, `WORD_LENGTH`, `HINT_PENALTY`)
- **Module globals:** Leading underscore for private state (`_state`, `_games`, `_current_by_user`)

### Patterns
- **In-memory state + periodic saves:** Modules load JSON on import, mutate in-memory dict, call `_persist()` to save
- **Date keys:** `YYYY-MM-DD` format strings for daily puzzle identification
- **Event keys:** Normalized lowercase alphanumeric strings (`undertale`, `deltarune`, `genshin`)
- **Composite keys:** Colon-separated strings (`{user_id}:{date_key}:{event_key}:{run_id}`)
- **Error handling:** Defensive checks, fallback values (e.g., `_state.get("games") or {}`)

## Testing

- **Framework:** pytest with pytest-asyncio for async support
- **Run command:** `pytest` (from project root)
- **Note:** Per commit history, tests may be incomplete ("pytest doesn't work so I'll manually test commits instead")
- **Manual testing recommended:** Use test Nerimity server with bot token

## Build & Deploy

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example.py .env
# Edit .env with NERIMITY_TOKEN, OWNER_USER_ID, REMINDER_CHANNEL_ID, REMINDER_CRON

# Run bot
python src_py/bot.py
```

### Runtime Requirements
- Bot token from Nerimity (get from nerimity.com)
- Channel ID for daily reminders
- Owner user ID for debug commands
- Writable `data/` directory (created automatically)

### Deployment
- No Docker (Dockerfile removed per commit history)
- No start.sh wrapper (removed per commit history)
- Direct execution: `python src_py/bot.py` in persistent process (screen, systemd, etc.)
- Bot will create `data/` directory and JSON files on first run

## Common Tasks

**Run bot:**
```bash
python src_py/bot.py
```

**Run tests:**
```bash
pytest
```

**Clean old leaderboard files:**
Bot automatically cleans files older than 30 days on startup (see `leaderboard_store.cleanup_old_leaderboard_files()`)

**Enable debug mode (owner only):**
Send `/debug code` in Nerimity (code is hardcoded as "code" in bot.py)

**Check game state manually:**
```bash
cat data/game-state.json | jq
```

**Add new event type:**
1. Add event definition in `src_py/events.py` EVENTS list
2. Add word pool in `src_py/word_list.py` (e.g., `_NEWEVENT_WORDS`)
3. Add command handler in `src_py/bot.py` (follow existing event command pattern)
4. Update help text and README

## Important Notes

### Data Persistence
- **All state in JSON files under `data/`** - do NOT edit while bot is running (data corruption risk)
- **Files created on-demand** - bot creates `data/` directory automatically if missing
- **Leaderboard files accumulate** - auto-cleaned after 30 days, but manual cleanup safe if bot stopped
- **Game state consolidated** - moved from per-game files to single `game-state.json` for performance

### XP & Leveling
- **100 levels total** with tier names (Newcomer → No Life)
- **XP formula:** Level 1-10 costs 8 XP/level, then +1 XP per 10 levels (level 11-20 = 9 XP/level, etc.)
- **Multipliers stack:** Hard mode (2x) × Streak bonus (1.0 + 0.1 per win) × Comeback bonus (2x if 7+ days away)
- **Owner user gets special level:** `"inf"` level with "Owner" tier (hardcoded in bot.py)

### Event System
- **Fixed events:** Undertale (Sept 15), Deltarune (Oct 31), Vocaloid (dynamic)
- **Dynamic events:** Genshin (42-day cycle from base date), Forsaken (manually set via owner command)
- **Event resolution:** Check date_key against event definitions, fallback to daily mode if no match
- **Event leaderboards:** Separate files with `-eventkey` suffix

### Hard Mode Rules
- **2x XP multiplier** applies to final result
- **No hints allowed** - hint button disabled in hard mode
- **Must reuse green letters** in exact positions
- **Must include yellow letters** somewhere in guess
- **Validation on every guess** - invalid guess rejected with feedback

### Duel Mode
- **No XP earned** - separate from daily progression
- **Turn-based:** Challenger → opponent alternate guesses
- **Same solution** for both players
- **30-minute timeout** per turn (DUEL_TIMEOUT constant)
- **Stored separately** from daily games

### Hints
- **Available after 2 guesses** (MIN_GUESSES_BEFORE_HINT)
- **Reveals 1-2 letters** depending on guess count
- **Costs 2 guesses** toward final score (HINT_PENALTY)
- **Disabled in hard mode**
- **One hint per game** (hintUsed flag prevents multiple hints)

### Word Lists
- **Daily:** ~500 curated English words (WORDS in word_list.py)
- **Genshin:** 5-letter character aliases (AYAKA, HUTAO, KAZUH, TARTA, etc.)
- **Undertale/Deltarune:** Character and term lists
- **Forsaken:** Roblox Forsaken character codes (NOOBB, SLASH, JOHND, etc.)
- **Vocaloid:** Vocaloid character names (MIKUU, TETOO, LUKAA, etc.)
- **Solution selection:** Hash-based deterministic selection from user_id + date_key + run_id

### Command Locking (Debug Mode)
- Owner can lock individual commands to prevent abuse
- `/debug code` enables debug mode
- `/lock commandname` disables command for all users
- `/unlock commandname` re-enables command
- Locked commands return "This command is locked" message

### Cron Reminders
- **Daily reminders** sent to configured channel
- **Cron expression** from REMINDER_CRON env var (default: 03:00 UTC = 07:00 Asia/Dubai)
- **Message:** Generic "Go play your daily Wordle!" prompt
- **Requires:** REMINDER_CHANNEL_ID set in .env

## Areas of Interest

### Complex Logic Worth Noting

1. **Game state resolution** (`game_logic.py:_get_or_init_state`): 
   - Checks if user's current state matches requested date/event
   - Auto-increments runId for new attempts on same date
   - Normalizes event keys for consistent lookups

2. **Leaderboard notifier** (`leaderboard_notifier.py`):
   - Tracks message IDs of posted leaderboards
   - Re-edits existing messages when new results come in
   - Prunes old message tracking after 48 hours

3. **Comeback bonus** (`xp_store.py`):
   - Tracks last play date per user
   - Applies 2x multiplier if 7+ days since last play
   - One-time bonus per return (resets after next play)

4. **Genshin countdown** (`genshin_countdown.py`):
   - Calculates next update date from base date + 42-day cycles
   - Auto-refreshes countdown data on bot startup
   - Handles version numbering (4.0, 4.1, 4.2, etc.)

5. **Hard mode validation** (`game_logic.py:make_guess`):
   - Validates guesses against known green positions
   - Checks for inclusion of all yellow letters
   - Returns specific error messages for violations

6. **Streak tracking** (`stats.py:get_current_streak`):
   - Scans completed games chronologically
   - Detects breaks in consecutive wins
   - Separate streaks for daily vs event modes

### Potential Gotchas

- **Concurrent writes:** No locking on JSON files - concurrent bot instances will corrupt data
- **SDK event patching:** bot.py patches SDK gateway events to add "message:button_clicked" support (lines 64-66)
- **State mutation patterns:** Stores load on import, so module reloading won't pick up external file changes
- **Date keys timezone:** Uses UTC (datetime.now(timezone.utc)), so daily puzzles roll over at midnight UTC
- **Owner ID check:** String comparison with `str()` coercion, so format matters ("123" vs 123)
- **Game key normalization:** Event keys normalized to lowercase alphanumeric - "Genshin-Impact" becomes "genshinimpact"

---

**Generated by:** Mistral Vibe init skill  
**Codebase analyzed:** 19 Python files, 3136 total lines  
**Last verified:** 2026-06-17
