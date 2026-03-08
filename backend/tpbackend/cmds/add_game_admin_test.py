"""
Tests for AddGameAdminCommand (!add_game / !ag).

Key scenarios covered:
- Empty / whitespace-only input
- Successful add (no name collision): guard returns None, Game.create() is called
- Duplicate blocked: same name already in DB (any release_year)
- Duplicate blocked: same name with a release year already in DB
- Input whitespace is stripped before lookup and creation
"""

from unittest.mock import MagicMock, patch

import pytest

from tpbackend.cmds.add_game_admin import AddGameAdminCommand

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def cmd():
    return AddGameAdminCommand()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_empty_input(cmd, make_user):
    result = cmd.execute(make_user(), "")
    assert "No game name provided" in result


def test_whitespace_only_input(cmd, make_user):
    result = cmd.execute(make_user(), "   ")
    assert "No game name provided" in result


# ---------------------------------------------------------------------------
# Happy path — no collision
# ---------------------------------------------------------------------------


def test_new_game_added_successfully(cmd, make_user):
    new_game = MagicMock()
    new_game.name = "Half-Life"
    new_game.id = 7

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None  # no duplicate
        mock_game_cls.create.return_value = new_game
        result = cmd.execute(make_user(), "Half-Life")

    assert "✅" in result
    assert "Half-Life" in result
    assert "7" in result
    mock_game_cls.create.assert_called_once_with(name="Half-Life")


def test_input_whitespace_stripped(cmd, make_user):
    """Leading/trailing whitespace around the name is stripped before lookup and creation."""
    new_game = MagicMock()
    new_game.name = "Zelda"
    new_game.id = 3

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        mock_game_cls.create.return_value = new_game
        cmd.execute(make_user(), "  Zelda  ")

    # Both the guard query and creation should use the stripped name
    mock_game_cls.get_or_none.assert_called_once()
    mock_game_cls.create.assert_called_once_with(name="Zelda")


# ---------------------------------------------------------------------------
# Duplicate blocked: same name already exists (regardless of release year)
# ---------------------------------------------------------------------------


def test_duplicate_name_no_year_is_blocked(cmd, make_user, make_game):
    """
    A game with the same name and no release year already exists → error.
    Game.create() must not be called.
    """
    existing = make_game(id=21, name="Resident Evil 4")
    existing.release_year = None

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = existing
        result = cmd.execute(make_user(), "Resident Evil 4")

    assert "Error" in result
    assert "already exist" in result
    assert "21" in result
    mock_game_cls.create.assert_not_called()


def test_duplicate_name_with_year_is_also_blocked(cmd, make_user, make_game):
    """
    A game with the same name AND a release year already exists → also blocked.
    !add_game has no year parameter, so it cannot safely create a same-named
    game — use !add_sgdb for year-disambiguated duplicates instead.
    Game.create() must not be called.
    """
    existing = make_game(id=21, name="Resident Evil 4")
    existing.release_year = 2005

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = existing
        result = cmd.execute(make_user(), "Resident Evil 4")

    assert "Error" in result
    assert "already exist" in result
    assert "21" in result
    mock_game_cls.create.assert_not_called()
