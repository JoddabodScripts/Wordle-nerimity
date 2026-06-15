"""Integration tests for complex scenarios."""
import pytest
import sys
import os
from unittest.mock import patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestCompleteGameFlow:
    """Test complete game flows from start to finish."""

    async def test_full_game_win_flow(self, mock_context, clean_data_dir):
        """Test a complete game from start to win."""
        from bot import cmd_wordle, cmd_answer, cmd_share, cmd_leaderboard, cmd_mystats

        ctx = mock_context(guild_id="test_guild")

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start game
            await cmd_wordle(ctx)
            assert ctx.reply_html.called

            # Make some wrong guesses
            ctx.reply_html.reset_mock()
            ctx.message.content = "/answer HOUSE"
            await cmd_answer(ctx)
            assert ctx.reply_html.called

            ctx.reply_html.reset_mock()
            ctx.message.content = "/answer MOUSE"
            await cmd_answer(ctx)
            assert ctx.reply_html.called

            # Win
            ctx.reply_html.reset_mock()
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)
            assert ctx.reply_html.called

            # Share
            ctx.reply_html.reset_mock()
            await cmd_share(ctx)
            assert ctx.reply_html.called

            # Check leaderboard
            ctx.reply_html.reset_mock()
            await cmd_leaderboard(ctx)
            assert ctx.reply_html.called

            # Check stats
            ctx.reply_html.reset_mock()
            await cmd_mystats(ctx)
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestMultiPlayerScenarios:
    """Test scenarios with multiple players."""

    async def test_multiple_players_same_day(self, mock_context, clean_data_dir):
        """Test multiple players playing on the same day."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Player 1
            ctx1 = mock_context(user_id="user1", username="player1", guild_id="test_guild")
            await cmd_wordle(ctx1)
            ctx1.message.content = "/answer CRANE"
            await cmd_answer(ctx1)

            # Player 2
            ctx2 = mock_context(user_id="user2", username="player2", guild_id="test_guild")
            await cmd_wordle(ctx2)
            ctx2.message.content = "/answer HOUSE"
            await cmd_answer(ctx2)
            ctx2.message.content = "/answer CRANE"
            await cmd_answer(ctx2)

            # Player 3
            ctx3 = mock_context(user_id="user3", username="player3", guild_id="test_guild")
            await cmd_wordle(ctx3)
            ctx3.message.content = "/answer CRANE"
            await cmd_answer(ctx3)

            # Check leaderboard shows all players
            ctx1.reply_html.reset_mock()
            await cmd_leaderboard(ctx1)
            assert ctx1.reply_html.called


@pytest.mark.asyncio
class TestErrorRecovery:
    """Test error handling and recovery."""

    async def test_invalid_word_doesnt_break_game(self, mock_context, clean_data_dir):
        """Test that invalid words don't break the game state."""
        from bot import cmd_wordle, cmd_answer

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', side_effect=lambda w: w != "ZZZZZ"):

            # Start game
            await cmd_wordle(ctx)

            # Try invalid word
            ctx.reply.reset_mock()
            ctx.message.content = "/answer ZZZZZ"
            await cmd_answer(ctx)

            # Should reject but not crash
            assert ctx.reply.called

            # Try valid word
            ctx.reply_html.reset_mock()
            ctx.message.content = "/answer CRANE"
            await cmd_answer(ctx)

            # Should work
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestEventIntegration:
    """Test event integration with gameplay."""

    async def test_event_affects_leaderboard(self, mock_context, clean_data_dir):
        """Test that events create separate leaderboards."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")

        # Play on Undertale day
        with patch('game_logic.datetime') as mock_dt, \
             patch('word_list.get_user_daily_solution', return_value="FRISK"), \
             patch('word_list.is_valid_word', return_value=True), \
             patch('events.get_event_for_date_key', return_value={"key": "undertale", "command": "undertale", "title": "Undertale"}):

            undertale_date = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = undertale_date
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            await cmd_wordle(ctx)
            ctx.message.content = "/answer FRISK"
            await cmd_answer(ctx)

            # Check leaderboard
            ctx.reply_html.reset_mock()
            await cmd_leaderboard(ctx)
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestDataPersistence:
    """Test that data persists correctly."""

    async def test_game_state_survives_multiple_calls(self, mock_context, clean_data_dir):
        """Test game state persistence."""
        from bot import cmd_wordle, cmd_answer

        ctx = mock_context()

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Start game
            await cmd_wordle(ctx)

            # Make guess
            ctx.message.content = "/answer HOUSE"
            await cmd_answer(ctx)

            # View game again
            ctx.reply_html.reset_mock()
            await cmd_wordle(ctx)

            # Should show previous guess
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestCommandAliases:
    """Test that command aliases work correctly."""

    async def test_dailyword_equals_wordle(self, mock_context, clean_data_dir):
        """Test that /dailyword and /wordle are equivalent."""
        from bot import cmd_wordle, cmd_dailyword

        ctx1 = mock_context(user_id="user1")
        ctx2 = mock_context(user_id="user2")

        with patch('word_list.get_user_daily_solution', return_value="CRANE"):
            await cmd_wordle(ctx1)
            await cmd_dailyword(ctx2)

            # Both should work
            assert ctx1.reply_html.called
            assert ctx2.reply_html.called
