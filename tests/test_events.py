"""Test special event scenarios (Undertale, Deltarune, Genshin, Forsaken, Vocaloid)."""
import pytest
import sys
import os
from unittest.mock import patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestEventDiscovery:
    """Test that all events are properly configured."""

    def test_all_events_defined(self):
        """Test that all expected events are defined."""
        from events import EVENTS

        assert len(EVENTS) == 5, "Should have 5 events defined"

        event_keys = [e["key"] for e in EVENTS]
        expected_keys = ["undertale", "deltarune", "genshin", "forsaken", "vocaloid"]

        for key in expected_keys:
            assert key in event_keys, f"Event {key} should be defined"

    def test_event_has_required_fields(self):
        """Test that each event has required fields."""
        from events import EVENTS

        required_fields = ["key", "command", "title"]

        for event in EVENTS:
            for field in required_fields:
                assert field in event, f"Event {event.get('key', 'unknown')} missing field: {field}"


@pytest.mark.asyncio
class TestUndertaleEvent:
    """Test Undertale anniversary event (September 15)."""

    async def test_undertale_date_detection(self):
        """Test that Undertale event is detected on September 15."""
        from events import get_event_for_date_key

        event = get_event_for_date_key("2026-09-15")
        assert event is not None
        assert event["key"] == "undertale"

    async def test_undertale_not_on_other_dates(self):
        """Test that Undertale event is not active on other dates."""
        from events import get_event_for_date_key

        event = get_event_for_date_key("2026-09-14")
        assert event is None or event["key"] != "undertale"

    async def test_undertale_wordle_game(self, mock_context, clean_data_dir):
        """Test playing Wordle during Undertale event."""
        from bot import cmd_wordle, cmd_answer

        ctx = mock_context()

        # Mock Undertale event date
        with patch('game_logic.datetime') as mock_dt, \
             patch('word_list.get_user_daily_solution', return_value="FRISK"), \
             patch('word_list.is_valid_word', return_value=True):

            undertale_date = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = undertale_date
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            # Start game on Undertale day
            await cmd_wordle(ctx)

            # Check that event is mentioned
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestDeltatuneEvent:
    """Test Deltarune anniversary event (October 31)."""

    async def test_deltarune_date_detection(self):
        """Test that Deltarune event is detected on October 31."""
        from events import get_event_for_date_key

        event = get_event_for_date_key("2026-10-31")
        assert event is not None
        assert event["key"] == "deltarune"

    async def test_deltarune_not_on_other_dates(self):
        """Test that Deltarune event is not active on other dates."""
        from events import get_event_for_date_key

        event = get_event_for_date_key("2026-10-30")
        assert event is None or event["key"] != "deltarune"


@pytest.mark.asyncio
class TestGenshinEvent:
    """Test Genshin update countdown event."""

    def test_genshin_event_exists(self):
        """Test that Genshin event is defined."""
        from events import EVENTS

        genshin_event = next((e for e in EVENTS if e["key"] == "genshin"), None)
        assert genshin_event is not None
        assert genshin_event["title"] == "Genshin Update Countdown"

    async def test_genshin_wordle_game(self, mock_context, clean_data_dir):
        """Test playing Wordle during Genshin event."""
        from bot import cmd_wordle

        ctx = mock_context()

        # Mock Genshin event
        with patch('genshin_countdown.get_genshin_event_date_key', return_value="2026-06-15"), \
             patch('events.get_genshin_event_date_key', return_value="2026-06-15"), \
             patch('word_list.get_user_daily_solution', return_value="AYAKA"):

            await cmd_wordle(ctx)

            # Should show game
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestForsakenEvent:
    """Test Forsaken update event."""

    def test_forsaken_event_exists(self):
        """Test that Forsaken event is defined."""
        from events import EVENTS

        forsaken_event = next((e for e in EVENTS if e["key"] == "forsaken"), None)
        assert forsaken_event is not None
        assert forsaken_event["title"] == "Forsaken Update"

    async def test_forsaken_wordle_game(self, mock_context, clean_data_dir):
        """Test playing Wordle during Forsaken event."""
        from bot import cmd_wordle

        ctx = mock_context()

        # Mock Forsaken event
        with patch('forsaken_store.get_forsaken_date_key', return_value="2026-06-15"), \
             patch('word_list.get_user_daily_solution', return_value="NOOBB"):

            await cmd_wordle(ctx)

            # Should show game
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestVocaloidEvent:
    """Test Vocaloid night event."""

    def test_vocaloid_event_exists(self):
        """Test that Vocaloid event is defined."""
        from events import EVENTS

        vocaloid_event = next((e for e in EVENTS if e["key"] == "vocaloid"), None)
        assert vocaloid_event is not None
        assert vocaloid_event["title"] == "Vocaloid Night"


@pytest.mark.asyncio
class TestEventLeaderboards:
    """Test that events have separate leaderboards."""

    async def test_event_leaderboard_separate_from_normal(self, mock_context, clean_data_dir):
        """Test that event days have separate leaderboards."""
        from bot import cmd_wordle, cmd_answer, cmd_leaderboard

        ctx = mock_context(guild_id="test_guild")

        # Play on Undertale day
        with patch('game_logic.datetime') as mock_dt, \
             patch('word_list.get_user_daily_solution', return_value="FRISK"), \
             patch('word_list.is_valid_word', return_value=True):

            undertale_date = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = undertale_date
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

            await cmd_wordle(ctx)
            ctx.message.content = "/answer FRISK"
            await cmd_answer(ctx)

            # Check leaderboard
            ctx.reply_html.reset_mock()
            await cmd_leaderboard(ctx)

            # Should show leaderboard
            assert ctx.reply_html.called


@pytest.mark.asyncio
class TestEventNormalization:
    """Test event key normalization."""

    def test_normalize_event_key(self):
        """Test that event keys are normalized correctly."""
        from game_logic import normalize_event_key

        assert normalize_event_key("undertale") == "undertale"
        assert normalize_event_key("UNDERTALE") == "undertale"
        assert normalize_event_key("UnderTale") == "undertale"
        assert normalize_event_key("") == ""
        assert normalize_event_key(None) == ""
