"""Tests for SetGameCommand (!set_game)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.set_game import SetGameCommand
from tpbackend.storage.storage_v2 import Activity, Game


@pytest.fixture
def cmd():
    return SetGameCommand()


def test_too_few_args(cmd, make_user):
    result = cmd.execute(make_user(id="user1"), "badargs")
    assert "Invalid syntax" in result


def test_game_not_found(cmd, make_user):
    with patch.object(Game, "get_or_none", return_value=None):
        result = cmd.execute(make_user(id="user1"), "1 999")
    assert "Error" in result


def test_activity_not_found(cmd, make_user, make_game):
    game = make_game(2, "Donkey Kong")
    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(Activity, "get_or_none", return_value=None):
            result = cmd.execute(make_user(id="user1"), "999 2")
    assert "not found" in result


def test_cannot_change_other_users_activity(cmd, make_user, make_game, make_activity):
    user = make_user(id="user1")
    game = make_game(2, "Donkey Kong")
    act = make_activity(10, user=make_user(id="user2"))

    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(Activity, "get_or_none", return_value=act):
            result = cmd.execute(user, "10 2")
    assert "not yours" in result


def test_game_changed_successfully(cmd, make_user, make_game, make_activity):
    user = make_user(id="user1")
    game = make_game(2, "Donkey Kong")
    act = make_activity(11, user=user, game=make_game(1, "Old Game"))

    with patch.object(Game, "get_or_none", return_value=game):
        with patch.object(Activity, "get_or_none", return_value=act):
            result = cmd.execute(user, "11 2")
    assert "Donkey Kong" in result
