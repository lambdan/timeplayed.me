"""Tests for StartManualCommand (!start)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.start_manual import StartManualCommand
from tpbackend.storage.storage_v2 import Game, LiveActivity


@pytest.fixture
def cmd():
    return StartManualCommand()


def test_game_not_found(cmd, make_user):
    with patch.object(Game, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "999")
    assert "Error" in result


def test_already_running(cmd, make_user, make_game, make_live_activity):
    game = make_game(3, "Hollow Knight")
    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(LiveActivity, "get_or_none", return_value=make_live_activity()):
            result = cmd.execute(make_user(), "3")
    assert "already have a manual activity running" in result


def test_start_success(cmd, make_user, make_game):
    game = make_game(3, "Hollow Knight")
    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(LiveActivity, "get_or_none", return_value=None):
            with patch("tpbackend.cmds.start_manual.last_platform_for_game", return_value=None):
                with patch.object(LiveActivity, "create"):
                    result = cmd.execute(make_user(), "3")
    assert "Hollow Knight" in result
    assert "stop" in result
