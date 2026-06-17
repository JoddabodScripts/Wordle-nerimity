# Contributing to Wordle Bot

Thank you for your interest in contributing to the Wordle Bot! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

---

## Getting Started

### Prerequisites

- **Python 3.9+** (recommended 3.11+)
- **Git**
- A Nerimity bot token (get one from [Nerimity](https://nerimity.com))

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/wordle.git
   cd wordle
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/JoddabodScripts/Wordle-nerimity.git
   ```

---

## Development Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example.py .env
```

Edit `.env` and add your configuration:

```python
NERIMITY_TOKEN=your_bot_token_here
OWNER_USER_ID=your_user_id_here
REMINDER_CHANNEL_ID=your_channel_id_here
REMINDER_CRON=0 3 * * *
```

### 3. Run the Bot

```bash
python src_py/bot.py
```

---

## Project Structure

```
wordle/
├── src_py/                    # Python source code
│   ├── bot.py                 # Main bot entry point
│   ├── game_logic.py          # Core Wordle game logic
│   ├── game_state_store.py    # Game state persistence
│   ├── leaderboard_store.py   # Leaderboard data management
│   ├── stats.py               # User statistics and XP system
│   ├── word_list.py           # Word lists for all game modes
│   ├── xp_store.py            # XP and comeback bonus logic
│   ├── duel_store.py          # Duel/versus mode logic
│   ├── events.py              # Event definitions (Genshin, etc.)
│   └── ...                    # Other modules
├── data/                      # JSON data files (generated at runtime)
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
└── README.md                  # Project overview

```

### Key Modules

- **bot.py**: Command handlers, event listeners, main bot loop
- **game_logic.py**: Wordle game rules, guess evaluation, hint system
- **leaderboard_store.py**: Daily and event leaderboards, result recording
- **stats.py**: XP calculation, leveling system, all-time stats
- **word_list.py**: Word pools for daily mode and special events
- **events.py**: Event definitions (Undertale, Deltarune, Genshin, Forsaken, Vocaloid)

---

## Coding Standards

### Python Style

- Follow **PEP 8** style guidelines
- Use **4 spaces** for indentation (no tabs)
- Use **type hints** where appropriate

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private functions**: `_leading_underscore`

### Example

```python
from typing import Optional

MAX_GUESSES = 6  # Constant

def make_guess(user_id: str, guess_raw: str, user_label: Optional[str] = None) -> dict:
    """
    Process a user's guess and update game state.
    
    Args:
        user_id: The user's unique ID
        guess_raw: The raw guess input
        user_label: Optional display name for the user
        
    Returns:
        Dictionary containing game state and feedback
    """
    guess = _normalize_guess(guess_raw)  # Private helper
    # ...
```

### Code Quality

- **Write docstrings** for all public functions and classes
- **Add comments** for complex logic
- **Keep functions small** and focused (single responsibility)
- **Avoid magic numbers** — use named constants
- **Handle errors gracefully** with try-except blocks

---

## Submitting Changes

### Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, focused commits:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

3. **Keep your fork updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub

### Commit Messages

Write clear, descriptive commit messages:

- **Good**: `fix: correct XP calculation for hard mode wins`
- **Good**: `feat: add weekly leaderboard support`
- **Good**: `docs: update README with new commands`
- **Bad**: `fix stuff`
- **Bad**: `update`

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

### Pull Request Guidelines

- **Describe your changes** clearly in the PR description
- **Reference related issues** (e.g., "Fixes #123")
- **Keep PRs focused** — one feature/fix per PR
- **Update documentation** if you change functionality
- **Ensure tests pass** before submitting
- **Be responsive** to review feedback

---

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Description**: What happened vs. what you expected
2. **Steps to reproduce**: Detailed steps to trigger the bug
3. **Environment**: Python version, OS, bot version
4. **Logs**: Any relevant error messages or stack traces
5. **Screenshots**: If applicable

### Feature Requests

For feature requests, please include:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Have you considered other approaches?
4. **Impact**: Who would benefit from this feature?

---

## Development Tips

### Debugging

- Set `DEBUG=1` in your `.env` for verbose logging
- Check `data/game-state.json` to inspect game state directly

### Testing Locally

- Create a test server on Nerimity
- Invite your bot to the test server
- Use multiple test accounts to test multiplayer features

### Working with Game State

The bot stores data in JSON files under `data/`:
- `game-state.json` - Active and completed games
- `leaderboard-YYYY-MM-DD.json` - Daily leaderboards
- `xpState.json` - Comeback bonus tracking

**Warning**: Editing these files directly while the bot is running may cause data corruption.

### Adding New Events

To add a new event type:

1. Add the event definition in `events.py`
2. Create the word list in `word_list.py`
3. Add the command handler in `bot.py`
4. Update help text and documentation

---

## Code of Conduct

- **Be respectful** and constructive in discussions
- **Welcome newcomers** and help them get started
- **Focus on the code**, not the person
- **Assume good intentions**

---

## Questions?

If you have questions not covered here:

- Open an issue labeled `question`
- Check existing issues and PRs
- Review the code documentation

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing!** 🎉
