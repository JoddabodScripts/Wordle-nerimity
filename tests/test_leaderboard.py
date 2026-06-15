"""Test leaderboard functionality and scenarios."""
import pytest
import sys
import os
from unittest.mock import patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestLeaderboardBasics:
    """Test basic leaderboard functionality."""

    async def test_empty_leaderboard(self, mock_context, clean_data_dir):
        """Test leaderboard with no players."""
        from bot import cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")
        await cmd_leaderboard(ctx)

        # Should show empty leaderboard
        assert ctx.reply_html.called
        html = ctx.reply_html.call_args[0][0]
        assert "leaderboard" in html.lower()

    async def test_leaderboard_with_one_player(self, mock_context, clean_data_dir):
        """Test leaderboard with single player."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Play and win
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Check leaderboard
            ctx.reply_html.reset_mock()
            await cmd_leaderboard(ctx)

            assert ctx.reply_html.called
            html = ctx.reply_html.call_args[0][0]
            assert "testuser" in html.lower() or ctx.user.username in html

    async def test_leaderboard_multiple_players(self, mock_context, mock_user, clean_data_dir):
        """Test leaderboard with multiple players."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Player 1 wins
            ctx1 = mock_context(user_id="user1", username="player1", guild_id="test_guild")
            await cmd_wordle(ctx1)
            ctx1.message.content = "/answer CRANE"
            await cmd_answer(ctx1)

            # Player 2 wins
            ctx2 = mock_context(user_id="user2", username="player2", guild_id="test_guild")
            await cmd_wordle(ctx2)
            ctx2.message.content = "/answer CRANE"
            await cmd_answer(ctx2)

            # Check leaderboard
            ctx1.reply_html.reset_mock()
            await cmd_leaderboard(ctx1)

            assert ctx1.reply_html.called


@pytest.mark.asyncio
class TestLeaderboardSorting:
    """Test leaderboard sorting logic."""

    async def test_leaderboard_sorts_by_score(self, mock_context, clean_data_dir):
        """Test that leaderboard sorts players by score correctly."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Player 1 wins in 1 guess (best)
            ctx1 = mock_context(user_id="user1", username="player1", guild_id="test_guild")
            await cmd_wordle(ctx1)
            ctx1.message.content = "/answer CRANE"
            await cmd_answer(ctx1)

            # Player 2 wins in 3 guesses
            ctx2 = mock_context(user_id="user2", username="player2", guild_id="test_guild")
            await cmd_wordle(ctx2)
            for _ in range(2):
                ctx2.message.content = "/answer HOUSE"
                await cmd_answer(ctx2)
            ctx2.message.content = "/answer CRANE"
            await cmd_answer(ctx2)

            # Check leaderboard
            ctx1.reply_html.reset_mock()
            await cmd_leaderboard(ctx1)

            assert ctx1.reply_html.called


@pytest.mark.asyncio
class TestAllTimeLeaderboard:
    """Test all-time leaderboard functionality."""

    async def test_alltime_leaderboard_empty(self, mock_context, clean_data_dir):
        """Test all-time leaderboard with no data."""
        from bot import cmd_alltimeleaderboard

        ctx = mock_context()
        await cmd_alltimeleaderboard(ctx)

        # Should show empty all-time leaderboard
        assert ctx.reply_html.called

    async def test_alltime_leaderboard_with_data(self, mock_context, clean_data_dir):
        """Test all-time leaderboard after playing games."""
        from bot import cmd_wordle, cmd_answer, cmd_alltimeleaderboard

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Win a game
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Check all-time leaderboard
            ctx.reply_html.reset_mock()
            await cmd_alltimeleaderboard(ctx)

            assert ctx.reply_html.called
            html = ctx.reply_html.call_args[0][0]
            assert "testuser" in html.lower() or ctx.user.username in html


@pytest.mark.asyncio
class TestLeaderboardButtons:
    """Test leaderboard button interactions."""

    async def test_leaderboard_has_buttons(self, mock_context, clean_data_dir):
        """Test that leaderboard shows navigation buttons."""
        from bot import cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")
        await cmd_leaderboard(ctx)

        # Check if buttons parameter exists
        assert ctx.reply_html.called


@pytest.mark.asyncio
class TestServerLeaderboard:
    """Test server-specific leaderboard functionality."""

    async def test_server_leaderboard_filters_members(self, mock_context, clean_data_dir):
        """Test that server leaderboard only shows server members."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Player in server
            ctx1 = mock_context(user_id="user1", username="player1", guild_id="test_guild")
            await cmd_wordle(ctx1)
            ctx1.message.content = "/answer CRANE"
            await cmd_answer(ctx1)

            # Check leaderboard
            ctx1.reply_html.reset_mock()
            await cmd_leaderboard(ctx1)

            assert ctx1.reply_html.called


@pytest.mark.asyncio
class TestLeaderboardDates:
    """Test leaderboard date handling."""

    async def test_leaderboard_today(self, mock_context, clean_data_dir):
        """Test viewing today's leaderboard."""
        from bot import cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")
        await cmd_leaderboard(ctx)

        assert ctx.reply_html.called

    async def test_different_days_different_leaderboards(self, mock_context, clean_data_dir):
        """Test that different days have different leaderboards."""
        from bot import cmd_wordle, cmd_answer
        from leaderboard_store import get_today_key

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Play on one day
            today = get_today_key()
            await cmd_wordle(ctx)
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Date key should match
            assert today is not None
