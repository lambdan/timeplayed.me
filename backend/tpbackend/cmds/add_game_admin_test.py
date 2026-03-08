"""
Tests for AddGameAdminCommand (!add_game / !ag).

Key scenarios covered:
- Empty / whitespace-only input
- Successful add (no name collision)
- Duplicate blocked: same name with no release year already in DB
- Same name exists but existing game HAS a release year → allowed
- Input whitespace is stripped before lookup
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
        with patch(
            "tpbackend.cmds.add_game_admin.get_game_by_name_or_alias_or_create",
            return_value=new_game,
        ):
            result = cmd.execute(make_user(), "Half-Life")

    assert "✅" in result
    assert "Half-Life" in result
    assert "7" in result


def test_input_whitespace_stripped(cmd, make_user):
    """Leading/trailing whitespace around the name is stripped before use."""
    new_game = MagicMock()
    new_game.name = "Zelda"
    new_game.id = 3

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        with patch(
            "tpbackend.cmds.add_game_admin.get_game_by_name_or_alias_or_create",
            return_value=new_game,
        ) as mock_create:
            cmd.execute(make_user(), "  Zelda  ")
            # The name passed to the DB helper should be stripped
            mock_create.assert_called_once_with("Zelda")


# ---------------------------------------------------------------------------
# Duplicate blocked: same name, no release year
# ---------------------------------------------------------------------------


def test_duplicate_name_no_year_is_blocked(cmd, make_user, make_game):
    """
    A game with the same name and no release year already exists → error.
    This is the classic "add same game twice" case.
    """
    existing = make_game(id=21, name="Resident Evil 4")
    existing.release_year = None

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = existing
        with patch(
            "tpbackend.cmds.add_game_admin.get_game_by_name_or_alias_or_create"
        ) as mock_create:
            result = cmd.execute(make_user(), "Resident Evil 4")

    assert "Error" in result
    assert "already exist" in result
    assert "21" in result
    mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# Same name, existing HAS a release year → allowed
# ---------------------------------------------------------------------------


def test_same_name_existing_has_year_allowed(cmd, make_user):
    """
    'Resident Evil 4' (2005) is already in the DB with a release year.
    Adding another entry with the same name is allowed because the DB query
    (name=X AND release_year IS NULL) returns nothing.
    """
    new_game = MagicMock()
    new_game.name = "Resident Evil 4"
    new_game.id = 99

    with patch("tpbackend.cmds.add_game_admin.Game") as mock_game_cls:
        # The existing game has a year, so the IS NULL filter finds nothing
        mock_game_cls.get_or_none.return_value = None
        with patch(
            "tpbackend.cmds.add_game_admin.get_game_by_name_or_alias_or_create",
            return_value=new_game,
        ):
            result = cmd.execute(make_user(), "Resident Evil 4")

    assert "✅" in result
    assert "Resident Evil 4" in result
