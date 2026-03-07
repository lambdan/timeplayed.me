"""Tests for SetGameAdminCommand (!adm_set_game) — admin only."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.set_game_admin import SetGameAdminCommand
from tpbackend.storage.storage_v2 import Activity, Game


@pytest.fixture
def cmd():
    return SetGameAdminCommand()


def test_too_few_args(cmd, make_admin_user):
    result = cmd.execute(make_admin_user(), "onlyoneword")
    assert "Invalid syntax" in result


def test_game_not_found(cmd, make_admin_user):
    with patch.object(Game, "get_or_none", return_value=None):
        result = cmd.execute(make_admin_user(), "1 999")
    assert "Error" in result


def test_activity_not_found(cmd, make_admin_user, make_game):
    game = make_game(2, "Tetris")
    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(Activity, "get_or_none", return_value=None):
            result = cmd.execute(make_admin_user(), "999 2")
    assert "not found" in result


def test_admin_can_change_any_users_activity(cmd, make_admin_user, make_user, make_game, make_activity):
    game = make_game(2, "Tetris")
    act = make_activity(70, user=make_user(id="another_user"), game=make_game(1, "Pong"))

    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(Activity, "get_or_none", return_value=act):
            result = cmd.execute(make_admin_user(), "70 2")
    assert "Tetris" in result
