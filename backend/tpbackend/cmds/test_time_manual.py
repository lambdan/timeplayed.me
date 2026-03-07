"""Tests for TimeManualCommand (!time)."""

import datetime
from unittest.mock import patch

import pytest

import tpbackend.utils
from tpbackend.cmds.time_manual import TimeManualCommand
from tpbackend.storage.storage_v2 import LiveActivity


@pytest.fixture
def cmd():
    return TimeManualCommand()


def test_no_live_activity(cmd, make_user):
    with patch.object(LiveActivity, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "")
    assert "no manual activity running" in result


def test_shows_game_and_elapsed_time(cmd, make_user, make_game, make_live_activity):
    user = make_user()
    started = tpbackend.utils.now() - datetime.timedelta(hours=1)
    live = make_live_activity(user=user, game=make_game(1, "Elden Ring"), started=started)

    with patch.object(LiveActivity, "get_or_none", return_value=live):
        result = cmd.execute(user, "")

    assert "Elden Ring" in result
    assert "01:" in result
