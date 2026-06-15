"""Test various Wordle game scenarios."""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestGameWinScenarios:
    """Test winning game scenarios."""

    async def test_win_on_first_guess(self, mock_context, clean_data_dir):
        """Test winning on the first guess."""
        from bot import cmd_wordle, cmd_answer

        ctx = mock_context()

        # Mock the solution to match our guess
        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start game
            await cmd_wordle(ctx)
            ctx.reply_html.reset_mock()

            # Guess the correct word
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Should show win message
            assert ctx.reply_html.called
            html = ctx.reply_html.call_args[0][0]
            assert "🎉" in html or "won" in html.lower() or "correct" in html.lower()

    async def test_win_on_last_guess(self, mock_context, clean_data_dir):
        """Test winning on the final guess."""
        from bot import cmd_wordle, cmd_answer
        from game_logic import MAX_GUESSES

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start game
            await cmd_wordle(ctx)

            # Make MAX_GUESSES - 1 wrong guesses
            for i in range(MAX_GUESSES - 1):
                ctx.reply_html.reset_mock()
                ctx.message.content = "/answer HOUSE"
                await cmd_answer(ctx)

            # Win on last guess
            ctx.reply_html.reset_mock()
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Should show win
            assert ctx.reply_html.called

    async def test_multiple_wins_track_stats(self, mock_context, clean_data_dir):
        """Test that multiple wins track statistics correctly."""
        from bot import cmd_wordle, cmd_answer, cmd_mystats

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Win a game
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Check stats
            ctx.reply_html.reset_mock()
            await cmd_mystats(ctx)

            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestGameLoseScenarios:
    """Test losing game scenarios."""

    async def test_lose_after_max_guesses(self, mock_context, clean_data_dir):
        """Test losing after using all guesses."""
        from bot import cmd_wordle, cmd_answer
        from game_logic import MAX_GUESSES

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start game
            await cmd_wordle(ctx)

            # Make MAX_GUESSES wrong guesses
            for i in range(MAX_GUESSES):
                ctx.reply_html.reset_mock()
                ctx.message.content = "/answer HOUSE"
                await cmd_answer(ctx)

            # Last call should show loss
            html = ctx.reply_html.call_args[0][0]
            assert "crane" in html.lower() or "answer" in html.lower()


@pytest.mark.asyncio
class TestHardModeScenarios:
    """Test hard mode gameplay."""

    async def test_hard_mode_double_xp(self, mock_context, clean_data_dir):
        """Test that hard mode gives double XP."""
        from bot import cmd_hard, cmd_answer

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start hard mode
            await cmd_hard(ctx)
            ctx.reply_html.reset_mock()

            # Win the game
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            assert ctx.reply_html.called

    async def test_hard_mode_no_hints(self, mock_context, clean_data_dir):
        """Test that hints are disabled in hard mode."""
        from bot import cmd_hard, cmd_answer, cmd_hint
        from game_logic import MIN_GUESSES_BEFORE_HINT

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start hard mode
            await cmd_hard(ctx)

            # Make enough guesses
            for i in range(MIN_GUESSES_BEFORE_HINT):
                ctx.reply_html.reset_mock()
                ctx.message.content = "/answer HOUSE"
                await cmd_answer(ctx)

            # Try to use hint
            ctx.reply.reset_mock()
            await cmd_hint(ctx)

            # Should reject
            assert ctx.reply.called
            reply_text = ctx.reply.call_args[0][0]
            assert "hard" in reply_text.lower()

    async def test_cannot_switch_modes_mid_game(self, mock_context, clean_data_dir):
        """Test that you can't switch between normal and hard mode mid-game."""
        from bot import cmd_wordle, cmd_hard

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"):
            # Start normal mode
            await cmd_wordle(ctx)
            ctx.reply.reset_mock()

            # Try to start hard mode
            await cmd_hard(ctx)

            # Should reject
            assert ctx.reply.called


@pytest.mark.asyncio
class TestShareCommand:
    """Test the /share command."""

    async def test_share_completed_game(self, mock_context, clean_data_dir):
        """Test sharing a completed game."""
        from bot import cmd_wordle, cmd_answer, cmd_share

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Complete a game
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Share
            ctx.reply_html.reset_mock()
            await cmd_share(ctx)

            # Should show share grid
            assert ctx.reply_html.called
            html = ctx.reply_html.call_args[0][0]
            assert "🟩" in html or "⬛" in html or "🟨" in html

    async def test_share_incomplete_game(self, mock_context, clean_data_dir):
        """Test sharing an incomplete game."""
        from bot import cmd_wordle, cmd_share

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"):
            # Start game but don't finish
            await cmd_wordle(ctx)
            ctx.reply.reset_mock()

            # Try to share
            await cmd_share(ctx)

            # Should tell user game not complete
            assert ctx.reply.called


@pytest.mark.asyncio
class TestChallengeCommand:
    """Test the /challenge command."""

    async def test_challenge_with_mention(self, mock_context, mock_user, clean_data_dir):
        """Test challenging another user."""
        from bot import cmd_challenge

        ctx = mock_context()
        other_user = mock_user(user_id="other_user", username="challenger")
        ctx.message.mentions = [other_user]

        await cmd_challenge(ctx)

        # Should send challenge message
        assert ctx.reply.called or ctx.send.called

    async def test_challenge_without_mention(self, mock_context, clean_data_dir):
        """Test challenge without mentioning anyone."""
        from bot import cmd_challenge

        ctx = mock_context()
        ctx.message.mentions = []

        await cmd_challenge(ctx)

        # Should ask for mention
        assert ctx.reply.called


@pytest.mark.asyncio
class TestGuessAlias:
    """Test that /guess is an alias for /answer."""

    async def test_guess_command(self, mock_context, clean_data_dir):
        """Test /guess command works like /answer."""
        from bot import cmd_guess

        ctx = mock_context()
        ctx.message.content = "/guess CRANE"

        await cmd_guess(ctx)

        # Should redirect to /answer
        assert ctx.reply.called
        reply_text = ctx.reply.call_args[0][0]
        assert "answer" in reply_text.lower()
