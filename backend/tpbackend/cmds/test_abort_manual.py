"""Tests for AbortManualCommand (!abort)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.abort_manual import AbortManualCommand
from tpbackend.storage.storage_v2 import LiveActivity


@pytest.fixture
def cmd():
    return AbortManualCommand()


def test_no_live_activity(cmd, make_user):
    with patch.object(LiveActivity, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "")
    assert "no manual activity running" in result


def test_abort_shows_game_name(cmd, make_user, make_game, make_live_activity):
    user = make_user()
    live = make_live_activity(user=user, game=make_game(1, "Bloodborne"))

    with patch.object(LiveActivity, "get_or_none", return_value=live):
        result = cmd.execute(user, "")

    assert "Bloodborne" in result
