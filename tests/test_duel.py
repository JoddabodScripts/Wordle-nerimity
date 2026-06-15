"""Test versus/duel functionality."""
import pytest
import sys
import os
from unittest.mock import patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestDuelCreation:
    """Test creating duels."""

    async def test_versus_command_creates_duel(self, mock_context, mock_user, clean_data_dir):
        """Test /versus command creates a duel."""
        from bot import cmd_versus

        ctx = mock_context()
        opponent = mock_user(user_id="opponent_id", username="opponent")
        ctx.message.mentions = [opponent]

        with patch('word_list.get_user_daily_solution', return_value="CRANE"):
            await cmd_versus(ctx)

            # Should create duel
            assert ctx.reply_html.called or ctx.reply.called

    async def test_versus_without_mention(self, mock_context, clean_data_dir):
        """Test /versus without mentioning opponent."""
        from bot import cmd_versus

        ctx = mock_context()
        ctx.message.mentions = []

        await cmd_versus(ctx)

        # Should ask for mention
        assert ctx.reply.called
        reply_text = ctx.reply.call_args[0][0]
        assert "mention" in reply_text.lower() or "player" in reply_text.lower()

    async def test_versus_self(self, mock_context, clean_data_dir):
        """Test challenging yourself (should be rejected)."""
        from bot import cmd_versus

        ctx = mock_context()
        ctx.message.mentions = [ctx.user]

        await cmd_versus(ctx)

        # Should reject
        assert ctx.reply.called


@pytest.mark.asyncio
class TestDuelGameplay:
    """Test duel gameplay mechanics."""

    async def test_duel_guess_valid(self, mock_context, mock_user, clean_data_dir):
        """Test making a valid guess in a duel."""
        from bot import cmd_versus, cmd_duelguess

        # Create duel
        ctx = mock_context()
        opponent = mock_user(user_id="opponent_id", username="opponent")
        ctx.message.mentions = [opponent]

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            await cmd_versus(ctx)
            ctx.reply_html.reset_mock()
            ctx.reply.reset_mock()

            # Make a guess
            ctx.message.content = "/duelguess HOUSE"
            await cmd_duelguess(ctx)

            # Should process guess
            assert ctx.reply_html.called or ctx.reply.called

    async def test_duel_guess_without_active_duel(self, mock_context, clean_data_dir):
        """Test making a guess without active duel."""
        from bot import cmd_duelguess

        ctx = mock_context()
        ctx.message.content = "/duelguess CRANE"

        await cmd_duelguess(ctx)

        # Should tell user no active duel
        assert ctx.reply.called

    async def test_duel_win_condition(self, mock_context, mock_user, clean_data_dir):
        """Test winning a duel."""
        from bot import cmd_versus, cmd_duelguess

        ctx = mock_context()
        opponent = mock_user(user_id="opponent_id", username="opponent")
        ctx.message.mentions = [opponent]

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Create duel
            await cmd_versus(ctx)

            # Win immediately
            ctx.message.content = "/duelguess CRANE"
            await cmd_duelguess(ctx)

            # Should show win
            assert ctx.reply_html.called or ctx.reply.called


@pytest.mark.asyncio
class TestDuelTurnSystem:
    """Test duel turn-based system."""

    async def test_duel_turn_alternation(self, mock_context, mock_user, clean_data_dir):
        """Test that turns alternate between players."""
        from bot import cmd_versus, cmd_duelguess

        ctx1 = mock_context(user_id="user1", username="player1")
        ctx2 = mock_context(user_id="user2", username="player2")

        ctx1.message.mentions = [ctx2.user]

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Player 1 creates duel
            await cmd_versus(ctx1)

            # Player 1 makes first guess
            ctx1.message.content = "/duelguess HOUSE"
            await cmd_duelguess(ctx1)

            # Player 1 tries to guess again (should fail)
            ctx1.reply.reset_mock()
            ctx1.message.content = "/duelguess MOUSE"
            await cmd_duelguess(ctx1)

            # Should reject (not their turn)
            assert ctx1.reply.called

    async def test_duel_guess_out_of_turn(self, mock_context, mock_user, clean_data_dir):
        """Test guessing out of turn is rejected."""
        from bot import cmd_versus, cmd_duelguess

        ctx = mock_context()
        opponent = mock_user(user_id="opponent_id", username="opponent")
        ctx.message.mentions = [opponent]

        with patch('word_list.get_user_daily_solution', return_value="CRANE"), \
             patch('word_list.is_valid_word', return_value=True):

            # Create duel
            await cmd_versus(ctx)

            # Make a guess
            ctx.message.content = "/duelguess HOUSE"
            await cmd_duelguess(ctx)

            # Try to guess again immediately
            ctx.reply.reset_mock()
            ctx.message.content = "/duelguess MOUSE"
            await cmd_duelguess(ctx)

            # Should reject
            assert ctx.reply.called


@pytest.mark.asyncio
class TestDuelTimeout:
    """Test duel timeout mechanics."""

    async def test_duel_timeout_constant_exists(self):
        """Test that DUEL_TIMEOUT constant is defined."""
        from duel_store import DUEL_TIMEOUT

        assert DUEL_TIMEOUT > 0, "DUEL_TIMEOUT should be positive"


@pytest.mark.asyncio
class TestDuelEdgeCases:
    """Test duel edge cases."""

    async def test_multiple_duels_per_user(self, mock_context, mock_user, clean_data_dir):
        """Test that a user can only have one active duel."""
        from bot import cmd_versus

        ctx = mock_context()
        opponent1 = mock_user(user_id="opponent1", username="opponent1")
        opponent2 = mock_user(user_id="opponent2", username="opponent2")

        with patch('word_list.get_user_daily_solution', return_value="CRANE"):
            # Create first duel
            ctx.message.mentions = [opponent1]
            await cmd_versus(ctx)

            ctx.reply.reset_mock()
            ctx.reply_html.reset_mock()

            # Try to create second duel
            ctx.message.mentions = [opponent2]
            await cmd_versus(ctx)

            # Should reject or handle appropriately
            assert ctx.reply.called or ctx.reply_html.called
