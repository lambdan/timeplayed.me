"""Tests for StopManualCommand (!stop)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.stop_manual import StopManualCommand
from tpbackend.storage.storage_v2 import LiveActivity


@pytest.fixture
def cmd():
    return StopManualCommand()


def test_no_live_activity(cmd, make_user):
    with patch.object(LiveActivity, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "")
    assert "haven't started" in result


def test_stop_saves_activity(cmd, make_user, make_game, make_activity, make_live_activity):
    user = make_user()
    live = make_live_activity(user=user, game=make_game(1, "Ori"))
    saved = make_activity(1, seconds=3600, game=make_game(1, "Ori"))

    with patch.object(LiveActivity, "get_or_none", return_value=live):
        with patch("tpbackend.cmds.stop_manual.operations") as mock_ops:
            mock_ops.add_session.return_value = (saved, None)
            result = cmd.execute(user, "")

    assert "✅" in result
    assert "Ori" in result


def test_too_short_session_not_saved(cmd, make_user, make_game, make_live_activity):
    user = make_user()
    live = make_live_activity(user=user, game=make_game(1, "Ori"))

    with patch.object(LiveActivity, "get_or_none", return_value=live):
        with patch("tpbackend.cmds.stop_manual.operations") as mock_ops:
            mock_ops.add_session.return_value = (None, ValueError("too short"))
            result = cmd.execute(user, "")

    assert "too short" in result
