"""Pytest fixtures for Nerimity Wordle bot testing."""
import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Add src_py to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.fixture
def mock_user():
    """Create a mock Nerimity user."""
    def _create_user(user_id="test_user_123", username="testuser", tag="0001"):
        user = Mock()
        user.id = user_id
        user.username = username
        user.tag = tag
        user.discriminator = tag
        return user
    return _create_user


@pytest.fixture
def mock_message():
    """Create a mock Nerimity message."""
    def _create_message(content="", author=None):
        message = Mock()
        message.content = content
        message.author = author or Mock(id="test_user_123", username="testuser", tag="0001")
        message.id = f"msg_{hash(content)}"
        message.channel_id = "test_channel_123"
        return message
    return _create_message


@pytest.fixture
def mock_context(mock_user, mock_message):
    """Create a mock Nerimity command context."""
    def _create_context(user_id="test_user_123", username="testuser", content="", guild_id=None):
        ctx = Mock()
        user = mock_user(user_id=user_id, username=username)
        ctx.user = user
        ctx.author = user
        ctx.message = mock_message(content=content, author=user)
        ctx.channel_id = "test_channel_123"
        ctx.guild_id = guild_id

        # Mock reply methods
        ctx.reply = AsyncMock(return_value=mock_message(content="reply"))
        ctx.send = AsyncMock(return_value=mock_message(content="sent"))
        ctx.reply_html = AsyncMock(return_value=mock_message(content="html"))

        return ctx
    return _create_context


@pytest.fixture
def clean_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    with patch.dict(os.environ, {"DATA_DIR": str(data_dir)}):
        # Patch all store modules to use temp directory
        import game_state_store
        import leaderboard_store
        import duel_store
        import xp_store

        original_data_dir = game_state_store.DATA_DIR if hasattr(game_state_store, 'DATA_DIR') else None

        # Override DATA_DIR in all modules
        for module in [game_state_store, leaderboard_store, duel_store, xp_store]:
            if hasattr(module, 'DATA_DIR'):
                module.DATA_DIR = str(data_dir)

        yield data_dir

        # Restore original (if needed for cleanup)
        if original_data_dir:
            for module in [game_state_store, leaderboard_store, duel_store, xp_store]:
                if hasattr(module, 'DATA_DIR'):
                    module.DATA_DIR = original_data_dir


@pytest.fixture
def mock_bot():
    """Create a mock Nerimity bot instance."""
    bot = Mock()
    bot.token = "test_token"
    bot.prefix = "/"
    bot.commands = {}
    bot.events = {}

    # Mock command decorator
    def command_decorator(name, description=""):
        def decorator(func):
            bot.commands[name] = {
                "func": func,
                "description": description,
                "name": name
            }
            return func
        return decorator

    bot.command = command_decorator

    # Mock event decorator
    def on_decorator(event_name):
        def decorator(func):
            if event_name not in bot.events:
                bot.events[event_name] = []
            bot.events[event_name].append(func)
            return func
        return decorator

    bot.on = on_decorator

    return bot


@pytest.fixture
def fixed_date():
    """Fixture to mock datetime.now for consistent testing."""
    test_date = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    with patch('game_logic.datetime') as mock_dt:
        mock_dt.now.return_value = test_date
        mock_dt.utcnow.return_value = test_date
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield test_date


@pytest.fixture
def sample_words():
    """Provide sample word lists for testing."""
    return {
        "valid_words": ["CRANE", "AUDIO", "STARE", "HOUSE", "MOUSE", "GHOST", "PIANO"],
        "invalid_words": ["ZZZZZ", "QQQJJ", "XXXXX"],
        "test_solutions": {
            "easy": "CRANE",
            "medium": "HOUSE",
            "hard": "GHOST"
        }
    }


@pytest.fixture
def mock_word_list(sample_words):
    """Mock the word_list module."""
    with patch('word_list.get_user_daily_solution') as mock_solution, \
         patch('word_list.is_valid_word') as mock_valid:

        mock_solution.return_value = sample_words["test_solutions"]["easy"]
        mock_valid.side_effect = lambda word: word.upper() in sample_words["valid_words"]

        yield {
            "solution": mock_solution,
            "is_valid": mock_valid
        }


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all data stores between tests."""
    import game_state_store
    import leaderboard_store
    import duel_store

    # Clear any cached data
    yield

    # Cleanup after test


@pytest.fixture
def event_configs():
    """Provide event configurations for testing."""
    return {
        "undertale": {"key": "undertale", "date": "2026-09-15"},
        "deltarune": {"key": "deltarune", "date": "2026-10-31"},
        "genshin": {"key": "genshin", "date": None},  # Dynamic
        "forsaken": {"key": "forsaken", "date": None},  # Dynamic
        "vocaloid": {"key": "vocaloid", "date": None}
    }


@pytest.fixture
def discover_commands():
    """Discover all commands from bot.py."""
    import re

    bot_file = os.path.join(os.path.dirname(__file__), '..', 'src_py', 'bot.py')

    with open(bot_file, 'r') as f:
        content = f.read()

    # Find all @bot.command decorators
    command_pattern = r'@bot\.command\("([^"]+)"'
    commands = re.findall(command_pattern, content)

    # Find all @bot.command_private decorators
    private_pattern = r'@bot\.command_private\("([^"]+)"'
    private_commands = re.findall(private_pattern, content)

    return {
        "public": commands,
        "private": private_commands,
        "all": commands + private_commands
    }


@pytest.fixture
def discover_events():
    """Discover all events from bot.py."""
    import re

    bot_file = os.path.join(os.path.dirname(__file__), '..', 'src_py', 'bot.py')

    with open(bot_file, 'r') as f:
        content = f.read()

    # Find all @bot.on decorators
    event_pattern = r'@bot\.on\("([^"]+)"'
    events = re.findall(event_pattern, content)

    return events
