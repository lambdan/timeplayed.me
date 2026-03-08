"""
Tests for GetGameCommand (!get_game / !gg).
"""

import os
from unittest.mock import patch

import pytest

from tpbackend.cmds.get_game import GetGameCommand


@pytest.fixture
def cmd():
    return GetGameCommand()


def test_game_not_found(cmd, make_user):
    with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        mock_game_cls.id = None
        result = cmd.execute(make_user(), "999")
    assert "not found" in result


def test_game_found_basic(cmd, make_user, make_game):
    game = make_game(id=42, name="Half-Life")
    game.sgdb_id = None
    game.release_year = 1998
    with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        mock_game_cls.id = None
        result = cmd.execute(make_user(), "42")
    assert "Half-Life" in result
    assert "42" in result


def test_game_with_sgdb_id_shows_link(cmd, make_user, make_game):
    game = make_game(id=10, name="Portal")
    game.sgdb_id = 12345
    game.release_year = 2007
    with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        mock_game_cls.id = None
        result = cmd.execute(make_user(), "10")
    assert "steamgriddb.com/game/12345" in result


def test_game_without_sgdb_id_shows_none(cmd, make_user, make_game):
    game = make_game(id=10, name="Portal")
    game.sgdb_id = None
    game.release_year = 2007
    with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        mock_game_cls.id = None
        result = cmd.execute(make_user(), "10")
    assert "SGDB ID: None" in result


def test_game_page_link_shown_when_timeplayed_url_set(cmd, make_user, make_game):
    game = make_game(id=7, name="Doom")
    game.sgdb_id = None
    game.release_year = 1993
    with patch("tpbackend.cmds.get_game.game_url", return_value="https://timeplayed.me/game/7"):
        with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
            mock_game_cls.get_or_none.return_value = game
            mock_game_cls.id = None
            result = cmd.execute(make_user(), "7")
    assert "[7](https://timeplayed.me/game/7)" in result


def test_game_page_link_not_shown_when_timeplayed_url_empty(cmd, make_user, make_game):
    game = make_game(id=7, name="Doom")
    game.sgdb_id = None
    game.release_year = 1993
    with patch("tpbackend.cmds.get_game.game_url", return_value=""):
        with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
            mock_game_cls.get_or_none.return_value = game
            mock_game_cls.id = None
            result = cmd.execute(make_user(), "7")
    assert "/game/7" not in result
    assert "- ID: 7" in result


def test_game_page_link_trailing_slash_stripped(cmd, make_user, make_game):
    """game_url() returns a clean URL (no double slashes)."""
    game = make_game(id=5, name="Quake")
    game.sgdb_id = None
    game.release_year = 1996
    with patch("tpbackend.cmds.get_game.game_url", return_value="https://example.com/game/5"):
        with patch("tpbackend.cmds.get_game.Game") as mock_game_cls:
            mock_game_cls.get_or_none.return_value = game
            mock_game_cls.id = None
            result = cmd.execute(make_user(), "5")
    assert "[5](https://example.com/game/5)" in result
    assert "//game" not in result
