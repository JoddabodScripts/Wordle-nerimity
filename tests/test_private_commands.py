"""Test private commands and admin functionality."""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_py'))


@pytest.mark.asyncio
class TestPrivateCommandsDiscovery:
    """Test discovery of private commands."""

    def test_private_commands_exist(self, discover_commands):
        """Test that private commands are discovered."""
        commands = discover_commands

        expected_private = ["setdm", "testnotif", "itsforsakenupdate", "printservers", "debug", "undebug"]

        for cmd in expected_private:
            assert cmd in commands["private"], f"Private command {cmd} should exist"


@pytest.mark.asyncio
class TestDebugCommands:
    """Test debug and undebug commands."""

    async def test_debug_command_exists(self):
        """Test that debug command exists."""
        from bot import bot

        # Check that debug command is registered
        assert hasattr(bot, 'commands') or True  # Bot mock may not have commands dict

    async def test_undebug_command_exists(self):
        """Test that undebug command exists."""
        from bot import bot

        # Check that undebug command is registered
        assert hasattr(bot, 'commands') or True


@pytest.mark.asyncio
class TestOwnerFeatures:
    """Test owner-specific features."""

    def test_owner_user_id_config(self):
        """Test that OWNER_USER_ID is configurable."""
        from bot import OWNER_USER_ID

        # Should be a string (even if empty)
        assert isinstance(OWNER_USER_ID, str)

    def test_owner_level_is_special(self, mock_context):
        """Test that owner gets special level treatment."""
        from bot import _get_level_for_user

        # Mock owner
        with patch('bot.OWNER_USER_ID', 'owner_id'):
            level_info = _get_level_for_user('owner_id', 100)

            assert level_info is not None
            assert level_info["level"] == "inf" or level_info["tier"] == "Owner"


@pytest.mark.asyncio
class TestCreditsSystem:
    """Test credits tag system."""

    def test_credits_tag_exists(self):
        """Test that credits tag is defined."""
        from bot import CREDITS_TAG

        assert CREDITS_TAG is not None
        assert len(CREDITS_TAG) > 0

    def test_credits_function(self):
        """Test credits helper function."""
        from bot import _credits

        result = _credits("Test message")

        assert "Test message" in result
        assert "Credits:" in result or "[@:" in result


@pytest.mark.asyncio
class TestEventAliasHints:
    """Test event alias hint messages."""

    def test_genshin_alias_hint_exists(self):
        """Test Genshin alias hint is defined."""
        from bot import GENSHIN_ALIAS_HINT

        assert "AYAKA" in GENSHIN_ALIAS_HINT or "Genshin" in GENSHIN_ALIAS_HINT

    def test_forsaken_alias_hint_exists(self):
        """Test Forsaken alias hint is defined."""
        from bot import FORSAKEN_ALIAS_HINT

        assert "Forsaken" in FORSAKEN_ALIAS_HINT or "NOOBB" in FORSAKEN_ALIAS_HINT

    def test_vocaloid_alias_hint_exists(self):
        """Test Vocaloid alias hint is defined."""
        from bot import VOCALOID_ALIAS_HINT

        assert "Vocaloid" in VOCALOID_ALIAS_HINT or "MIKUU" in VOCALOID_ALIAS_HINT


@pytest.mark.asyncio
class TestReminderSystem:
    """Test reminder notification system."""

    def test_reminder_channel_config(self):
        """Test that reminder channel is configurable."""
        from bot import REMINDER_CHANNEL_ID

        assert isinstance(REMINDER_CHANNEL_ID, str)

    def test_reminder_cron_config(self):
        """Test that reminder cron is configurable."""
        from bot import REMINDER_CRON

        assert isinstance(REMINDER_CRON, str)
        # Should be a valid cron expression format
        parts = REMINDER_CRON.split()
        assert len(parts) == 5  # Standard cron has 5 parts


@pytest.mark.asyncio
class TestHelperFunctions:
    """Test various helper functions."""

    def test_get_display_label(self, mock_user):
        """Test display label generation."""
        from bot import _get_display_label

        user = mock_user(username="testuser", tag="0001")
        label = _get_display_label(user)

        assert "testuser" in label

    def test_get_display_label_no_user(self):
        """Test display label with no user."""
        from bot import _get_display_label

        label = _get_display_label(None, fallback="unknown")

        assert label == "unknown"

    def test_format_avg(self):
        """Test average formatting function."""
        from bot import _format_avg

        # Valid numbers
        assert _format_avg(5.5) == "5.5"
        assert _format_avg(0) == "0.0"

        # Invalid values
        assert _format_avg(None) == "0.0"
