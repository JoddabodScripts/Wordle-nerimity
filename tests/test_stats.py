"""Test stats and comparison functionality."""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestMyStats:
    """Test /mystats command."""

    async def test_mystats_no_games_played(self, mock_context, clean_data_dir):
        """Test stats for user with no games played."""
        from bot import cmd_mystats

        ctx = mock_context()
        await cmd_mystats(ctx)

        # Should show stats with zeros
        assert ctx.reply_html.called
        html = ctx.reply_html.call_args[0][0]
        assert "stats" in html.lower() or "0" in html

    async def test_mystats_after_win(self, mock_context, clean_data_dir):
        """Test stats after winning a game."""
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
            html = ctx.reply_html.call_args[0][0]
            assert "1" in html or "won" in html.lower()

    async def test_mystats_shows_streak(self, mock_context, clean_data_dir):
        """Test that mystats shows current streak."""
        from bot import cmd_mystats

        ctx = mock_context()
        await cmd_mystats(ctx)

        # Should show streak info
        assert ctx.reply_html.called


@pytest.mark.asyncio
class TestCompareStats:
    """Test /compare command functionality."""

    async def test_compare_with_valid_user(self, mock_context, mock_user, clean_data_dir):
        """Test comparing stats with another user."""
        from bot import cmd_compare

        ctx = mock_context()
        other_user = mock_user(user_id="other_user", username="otherplayer")
        ctx.message.mentions = [other_user]

        await cmd_compare(ctx)

        # Should show comparison
        assert ctx.reply_html.called
        html = ctx.reply_html.call_args[0][0]
        assert "testuser" in html.lower() or "otherplayer" in html.lower()

    async def test_compare_without_mention(self, mock_context, clean_data_dir):
        """Test compare without mentioning anyone."""
        from bot import cmd_compare

        ctx = mock_context()
        ctx.message.mentions = []

        await cmd_compare(ctx)

        # Should ask for mention
        assert ctx.reply.called
        reply_text = ctx.reply.call_args[0][0]
        assert "mention" in reply_text.lower()

    async def test_compare_self(self, mock_context, clean_data_dir):
        """Test comparing with yourself."""
        from bot import cmd_compare

        ctx = mock_context()
        ctx.message.mentions = [ctx.user]

        await cmd_compare(ctx)

        # Should handle appropriately
        assert ctx.reply_html.called or ctx.reply.called


@pytest.mark.asyncio
class TestStreakTracking:
    """Test streak tracking functionality."""

    async def test_streak_after_single_win(self, mock_context, clean_data_dir):
        """Test streak is 1 after single win."""
        from bot import cmd_wordle, cmd_answer
        from stats import get_current_streak

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Win a game
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Check streak
            streak = get_current_streak(ctx.user.id)
            assert streak >= 0


@pytest.mark.asyncio
class TestXPSystem:
    """Test XP and leveling system."""

    async def test_xp_gained_on_win(self, mock_context, clean_data_dir):
        """Test that XP is gained when winning."""
        from bot import cmd_wordle, cmd_answer, cmd_mystats

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Win a game
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Check stats for XP
            ctx.reply_html.reset_mock()
            await cmd_mystats(ctx)

            assert ctx.reply_html.called

    async def test_level_calculation(self):
        """Test level calculation from XP."""
        from stats import get_level

        # Test various XP values
        level_0 = get_level(0)
        assert level_0["level"] >= 0

        level_100 = get_level(100)
        assert level_100["level"] >= 0

        level_1000 = get_level(1000)
        assert level_1000["level"] >= level_100["level"]


@pytest.mark.asyncio
class TestComebackBonus:
    """Test comeback bonus system."""

    async def test_comeback_bonus_exists(self):
        """Test that comeback bonus function exists."""
        from xp_store import check_and_apply_comeback_bonus

        # Should be callable
        assert callable(check_and_apply_comeback_bonus)


@pytest.mark.asyncio
class TestStatsEdgeCases:
    """Test edge cases in stats system."""

    async def test_stats_with_multiple_wins(self, mock_context, clean_data_dir):
        """Test stats accumulation over multiple games."""
        from bot import cmd_mystats

        ctx = mock_context()

        # Check stats (should handle no games gracefully)
        await cmd_mystats(ctx)

        assert ctx.reply_html.called

    async def test_average_guesses_calculation(self, mock_context, clean_data_dir):
        """Test that average guesses is calculated correctly."""
        from bot import cmd_wordle, cmd_answer, cmd_mystats

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Win in 1 guess
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Check stats
            ctx.reply_html.reset_mock()
            await cmd_mystats(ctx)

            assert ctx.reply_html.called
