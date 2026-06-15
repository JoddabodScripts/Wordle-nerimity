"""Test all bot commands by auto-discovery."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestCommandDiscovery:
    """Test that all commands are discovered and callable."""

    def test_discover_all_commands(self, discover_commands):
        """Test that we can discover all commands from bot.py."""
        commands = discover_commands

        assert len(commands["public"]) > 0, "Should discover public commands"
        assert len(commands["private"]) > 0, "Should discover private commands"

        # Expected public commands
        expected_public = [
            "whelp", "wordle", "dailyword", "hard", "answer", "guess",
            "hint", "giveup", "share", "challenge", "leaderboard",
            "alltimeleaderboard", "mystats", "compare", "versus", "duelguess"
        ]

        for cmd in expected_public:
            assert cmd in commands["public"], f"Command {cmd} should be discovered"

        # Expected private commands
        expected_private = ["setdm", "testnotif", "itsforsakenupdate", "printservers", "debug", "undebug"]

        for cmd in expected_private:
            assert cmd in commands["private"], f"Private command {cmd} should be discovered"

    def test_discover_all_events(self, discover_events):
        """Test that we can discover all event handlers."""
        events = discover_events

        assert len(events) > 0, "Should discover event handlers"

        # Expected events
        expected_events = ["ready", "message:button_clicked", "message:created"]

        for event in expected_events:
            assert event in events, f"Event {event} should be discovered"


@pytest.mark.asyncio
class TestBasicCommands:
    """Test basic command functionality."""

    async def test_whelp_command(self, mock_context):
        """Test /whelp command shows help."""
        from bot import cmd_whelp

        ctx = mock_context()
        await cmd_whelp(ctx)

        ctx.reply_html.assert_called_once()
        call_args = ctx.reply_html.call_args
        assert call_args is not None
        html_content = call_args[0][0]
        assert "wordle" in html_content.lower()
        assert "leaderboard" in html_content.lower()

    async def test_wordle_command_new_game(self, mock_context, clean_data_dir, mock_word_list):
        """Test /wordle command starts a new game."""
        from bot import cmd_wordle

        ctx = mock_context()
        await cmd_wordle(ctx)

        # Should reply with HTML board
        ctx.reply_html.assert_called_once()
        call_args = ctx.reply_html.call_args
        assert call_args is not None

    async def test_dailyword_alias(self, mock_context, clean_data_dir, mock_word_list):
        """Test /dailyword is an alias for /wordle."""
        from bot import cmd_dailyword

        ctx = mock_context()
        await cmd_dailyword(ctx)

        ctx.reply_html.assert_called_once()


@pytest.mark.asyncio
class TestAnswerCommand:
    """Test the /answer command with various inputs."""

    async def test_answer_valid_word(self, mock_context, clean_data_dir, mock_word_list):
        """Test /answer with a valid word."""
        from bot import cmd_wordle, cmd_answer

        ctx = mock_context()

        # Start game first
        await cmd_wordle(ctx)
        ctx.reply_html.reset_mock()

        # Make a guess
        ctx.message.content = "/answer CRANE"
        await cmd_answer(ctx)

        # Should reply with updated board
        assert ctx.reply_html.called or ctx.reply.called

    async def test_answer_without_word(self, mock_context, clean_data_dir):
        """Test /answer without providing a word."""
        from bot import cmd_answer

        ctx = mock_context()
        ctx.message.content = "/answer"

        await cmd_answer(ctx)

        # Should ask for a word
        ctx.reply.assert_called_once()
        assert "please provide" in ctx.reply.call_args[0][0].lower() or \
               "word" in ctx.reply.call_args[0][0].lower()

    async def test_answer_invalid_length(self, mock_context, clean_data_dir):
        """Test /answer with wrong length word."""
        from bot import cmd_answer

        ctx = mock_context()
        ctx.message.content = "/answer ABC"

        await cmd_answer(ctx)

        # Should reject
        ctx.reply.assert_called_once()

    async def test_answer_invalid_word(self, mock_context, clean_data_dir, mock_word_list):
        """Test /answer with invalid word."""
        from bot import cmd_wordle, cmd_answer

        ctx = mock_context()

        # Start game
        await cmd_wordle(ctx)
        ctx.reply.reset_mock()
        ctx.reply_html.reset_mock()

        # Try invalid word
        ctx.message.content = "/answer ZZZZZ"
        await cmd_answer(ctx)

        # Should reject
        assert ctx.reply.called

    async def test_answer_no_active_game(self, mock_context, clean_data_dir):
        """Test /answer without starting a game first."""
        from bot import cmd_answer

        ctx = mock_context()
        ctx.message.content = "/answer CRANE"

        await cmd_answer(ctx)

        # Should tell user to start game first
        ctx.reply.assert_called_once()


@pytest.mark.asyncio
class TestHintCommand:
    """Test the /hint command."""

    async def test_hint_too_early(self, mock_context, clean_data_dir, mock_word_list):
        """Test /hint before making enough guesses."""
        from bot import cmd_wordle, cmd_hint
        from game_logic import MIN_GUESSES_BEFORE_HINT

        ctx = mock_context()

        # Start game
        await cmd_wordle(ctx)
        ctx.reply.reset_mock()

        # Try hint immediately
        await cmd_hint(ctx)

        # Should reject
        ctx.reply.assert_called_once()
        reply_text = ctx.reply.call_args[0][0]
        assert str(MIN_GUESSES_BEFORE_HINT) in reply_text or "guess" in reply_text.lower()

    async def test_hint_after_guesses(self, mock_context, clean_data_dir, mock_word_list):
        """Test /hint after making enough guesses."""
        from bot import cmd_wordle, cmd_answer, cmd_hint
        from game_logic import MIN_GUESSES_BEFORE_HINT

        ctx = mock_context()

        # Start game
        await cmd_wordle(ctx)

        # Make enough guesses
        for i in range(MIN_GUESSES_BEFORE_HINT):
            ctx.reply_html.reset_mock()
            ctx.message.content = "/answer STARE"
            await cmd_answer(ctx)

        ctx.reply_html.reset_mock()
        ctx.reply.reset_mock()

        # Now try hint
        await cmd_hint(ctx)

        # Should provide hint
        assert ctx.reply_html.called or ctx.reply.called

    async def test_hint_no_active_game(self, mock_context, clean_data_dir):
        """Test /hint without active game."""
        from bot import cmd_hint

        ctx = mock_context()
        await cmd_hint(ctx)

        # Should tell user to start game
        ctx.reply.assert_called_once()


@pytest.mark.asyncio
class TestGiveUpCommand:
    """Test the /giveup command."""

    async def test_giveup_active_game(self, mock_context, clean_data_dir, mock_word_list):
        """Test /giveup with active game."""
        from bot import cmd_wordle, cmd_giveup

        ctx = mock_context()

        # Start game
        await cmd_wordle(ctx)
        ctx.reply_html.reset_mock()

        # Give up
        await cmd_giveup(ctx)

        # Should show result
        ctx.reply_html.assert_called_once()

    async def test_giveup_no_game(self, mock_context, clean_data_dir):
        """Test /giveup without active game."""
        from bot import cmd_giveup

        ctx = mock_context()
        await cmd_giveup(ctx)

        # Should tell user no active game
        ctx.reply.assert_called_once()


@pytest.mark.asyncio
class TestLeaderboardCommands:
    """Test leaderboard-related commands."""

    async def test_leaderboard_command(self, mock_context, clean_data_dir):
        """Test /leaderboard command."""
        from bot import cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")
        await cmd_leaderboard(ctx)

        # Should show leaderboard
        ctx.reply_html.assert_called_once()

    async def test_alltimeleaderboard_command(self, mock_context, clean_data_dir):
        """Test /alltimeleaderboard command."""
        from bot import cmd_alltimeleaderboard

        ctx = mock_context()
        await cmd_alltimeleaderboard(ctx)

        # Should show all-time leaderboard
        ctx.reply_html.assert_called_once()

    async def test_mystats_command(self, mock_context, clean_data_dir):
        """Test /mystats command."""
        from bot import cmd_mystats

        ctx = mock_context()
        await cmd_mystats(ctx)

        # Should show stats
        ctx.reply_html.assert_called_once()


@pytest.mark.asyncio
class TestCompareCommand:
    """Test the /compare command."""

    async def test_compare_with_valid_user(self, mock_context, mock_user, clean_data_dir):
        """Test /compare with a valid user mention."""
        from bot import cmd_compare

        ctx = mock_context()
        other_user = mock_user(user_id="other_user", username="otheruser")
        ctx.message.mentions = [other_user]

        await cmd_compare(ctx)

        # Should show comparison
        ctx.reply_html.assert_called_once()

    async def test_compare_without_mention(self, mock_context, clean_data_dir):
        """Test /compare without mentioning anyone."""
        from bot import cmd_compare

        ctx = mock_context()
        ctx.message.mentions = []

        await cmd_compare(ctx)

        # Should ask for mention
        ctx.reply.assert_called_once()
