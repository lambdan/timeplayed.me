"""
Tests for AddGameAdminCommand (!add_game / !ag).

Key scenarios covered:
- Empty / whitespace-only input
- Successful add (no name collision)
- Duplicate blocked: same name with null release year already in DB
- Same name exists but existing game HAS a release year → allowed (create new null-year entry)
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
        mock_game_cls.get_or_none.return_value = None  # no null-year duplicate
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
# Duplicate blocked: same name, null release year
# ---------------------------------------------------------------------------


def test_duplicate_name_no_year_is_blocked(cmd, make_user, make_game):
    """
    A game with the same name and no release year already exists → error.
    This is the classic "add same game twice" case.
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


# ---------------------------------------------------------------------------
# Same name, existing HAS a release year → allowed
# ---------------------------------------------------------------------------


def test_same_name_existing_has_year_allowed(cmd, make_user):
    """
    'Resident Evil 4' (2005) is already in the DB with a release year.
    Adding another entry with the same name is allowed — a new null-year game
    is created that the admin can later disambiguate via !sgry / !add_sgdb.
    """
    new_game = MagicMock()
    new_game.name = "Resident Evil 4"
    new_game.id = 99

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        # The (name == s) & release_year.is_null() query finds nothing
        mock_game_cls.get_or_none.return_value = None
        mock_game_cls.create.return_value = new_game
        result = cmd.execute(make_user(), "Resident Evil 4")

    assert "✅" in result
    assert "Resident Evil 4" in result
    assert "99" in result
    mock_game_cls.create.assert_called_once_with(name="Resident Evil 4")
