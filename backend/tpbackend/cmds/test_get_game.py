"""Tests for GetGameCommand (!get_game)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.get_game import GetGameCommand
from tpbackend.storage.storage_v2 import Game


@pytest.fixture
def cmd():
    return GetGameCommand()


def test_game_not_found(cmd, make_user):
    with patch.object(Game, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "999")
    assert "Error" in result


def test_game_found_shows_name(cmd, make_user, make_game):
    with patch.object(Game, "get_or_none", return_value=make_game(1, "Metroid")):
        result = cmd.execute(make_user(), "1")
    assert "Metroid" in result


def test_game_without_aliases_has_no_aliases_section(cmd, make_user, make_game):
    with patch.object(Game, "get_or_none", return_value=make_game(1, "Metroid")):
        result = cmd.execute(make_user(), "1")
    assert "Aliases" not in result


def test_game_with_alias_shows_alias(cmd, make_user, make_game):
    game = make_game(2, "Metroid", aliases=["Super Metroid"])
    with patch.object(Game, "get_or_none", return_value=game):
        result = cmd.execute(make_user(), "2")
    assert "Metroid" in result
    assert "Super Metroid" in result
