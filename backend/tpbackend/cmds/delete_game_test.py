"""
Tests for DeleteGameCommand (!delete_game / !del_game / !remove_game).
"""

from unittest.mock import MagicMock, patch

import pytest

from tpbackend.cmds.delete_game import DeleteGameCommand


@pytest.fixture
def cmd():
    return DeleteGameCommand()


def _mock_activities(total=0):
    result = MagicMock()
    result.total = total
    return result


def test_game_not_found(cmd, make_admin_user):
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        result = cmd.execute(make_admin_user(), "99")
    assert "not found" in result


def test_game_has_activities_returns_error(cmd, make_admin_user, make_game, mock_api):
    game = make_game(id=1, name="Half-Life")
    game.release_year = 1998
    mock_api.get_activities_impl.return_value = _mock_activities(total=5)
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        result = cmd.execute(make_admin_user(), "1")
    assert "has activities" in result


def test_no_confirm_shows_preview_with_year(cmd, make_admin_user, make_game, mock_api):
    game = make_game(id=2, name="Portal")
    game.release_year = 2007
    mock_api.get_activities_impl.return_value = _mock_activities(total=0)
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        result = cmd.execute(make_admin_user(), "2")
    assert "Portal" in result
    assert "2007" in result
    assert "y" in result
    assert "deleted" not in result
    game.delete_instance.assert_not_called()


def test_no_confirm_shows_preview_without_year(
    cmd, make_admin_user, make_game, mock_api
):
    game = make_game(id=3, name="NoYear Game")
    game.release_year = None
    mock_api.get_activities_impl.return_value = _mock_activities(total=0)
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        result = cmd.execute(make_admin_user(), "3")
    assert "NoYear Game" in result
    assert "y" in result
    assert "deleted" not in result
    game.delete_instance.assert_not_called()


def test_confirm_deletes_game_with_year(cmd, make_admin_user, make_game, mock_api):
    game = make_game(id=4, name="Doom")
    game.release_year = 1993
    mock_api.get_activities_impl.return_value = _mock_activities(total=0)
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        result = cmd.execute(make_admin_user(), "4 y")
    assert "Doom" in result
    assert "1993" in result
    assert "deleted" in result
    game.delete_instance.assert_called_once()


def test_confirm_deletes_game_without_year(cmd, make_admin_user, make_game, mock_api):
    game = make_game(id=5, name="Mystery Game")
    game.release_year = None
    mock_api.get_activities_impl.return_value = _mock_activities(total=0)
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        result = cmd.execute(make_admin_user(), "5 y")
    assert "Mystery Game" in result
    assert "deleted" in result
    game.delete_instance.assert_called_once()


def test_confirm_case_insensitive(cmd, make_admin_user, make_game, mock_api):
    game = make_game(id=6, name="Quake")
    game.release_year = 1996
    mock_api.get_activities_impl.return_value = _mock_activities(total=0)
    with patch("tpbackend.cmds.delete_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = game
        result = cmd.execute(make_admin_user(), "6 Y")
    assert "deleted" in result
    game.delete_instance.assert_called_once()
