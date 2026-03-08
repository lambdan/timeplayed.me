"""
Tests for SetGameReleaseYearCommand (!set_game_release_year / !sgry).

Key scenarios covered:
- Invalid syntax (wrong number of arguments)
- Game not found
- Successfully setting a specific year
- Successfully unsetting the year (to null)
- Conflict blocked: same name + same year already exists (non-null)
- Conflict blocked: unsetting to null when another same-named game already has null year
"""

from unittest.mock import MagicMock, patch

import pytest

from tpbackend.cmds.set_game_release_year import SetGameReleaseYearCommand

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def cmd():
    return SetGameReleaseYearCommand()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_invalid_syntax_too_few_args(cmd, make_user):
    result = cmd.execute(make_user(), "42")
    assert "Invalid syntax" in result


def test_invalid_syntax_too_many_args(cmd, make_user):
    result = cmd.execute(make_user(), "42 2005 extra")
    assert "Invalid syntax" in result


def test_game_not_found(cmd, make_user):
    with patch("tpbackend.cmds.set_game_release_year.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        result = cmd.execute(make_user(), "999 2005")
    assert "not found" in result


# ---------------------------------------------------------------------------
# Happy path — setting a specific year
# ---------------------------------------------------------------------------


def test_set_year_successfully(cmd, make_user, make_game):
    game = make_game(id=1, name="Resident Evil 4")
    game.release_year = None

    with patch("tpbackend.cmds.set_game_release_year.Game") as mock_game_cls:
        # First call: find the game by id. Second call: conflict check returns None.
        mock_game_cls.get_or_none.side_effect = [game, None]
        result = cmd.execute(make_user(), "1 2005")

    assert "Resident Evil 4" in result
    assert game.save.called
    assert game.release_year == 2005


# ---------------------------------------------------------------------------
# Happy path — unsetting the year (to null)
# ---------------------------------------------------------------------------


def test_unset_year_successfully(cmd, make_user, make_game):
    game = make_game(id=1, name="Dolphin")
    game.release_year = 2024

    with patch("tpbackend.cmds.set_game_release_year.Game") as mock_game_cls:
        # First call: find the game by id. Second call: null-conflict check returns None.
        mock_game_cls.get_or_none.side_effect = [game, None]
        result = cmd.execute(make_user(), "1 null")

    assert "Dolphin" in result
    assert game.save.called
    assert game.release_year is None


# ---------------------------------------------------------------------------
# Conflict: setting year when same name + same year already exists
# ---------------------------------------------------------------------------


def test_conflict_setting_year_blocked(cmd, make_user, make_game):
    """
    Game id1 has name 'Foo', release year null.
    Game id2 also has name 'Foo', release year 2005.
    Setting id1's year to 2005 must be blocked.
    """
    game = make_game(id=1, name="Foo")
    game.release_year = None
    conflict = make_game(id=2, name="Foo")
    conflict.release_year = 2005

    with patch("tpbackend.cmds.set_game_release_year.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [game, conflict]
        result = cmd.execute(make_user(), "1 2005")

    assert "Error" in result
    assert "2005" in result
    game.save.assert_not_called()


# ---------------------------------------------------------------------------
# Conflict: unsetting year to null when another same-named game already has null year
# ---------------------------------------------------------------------------


def test_conflict_unsetting_to_null_blocked(cmd, make_user, make_game):
    """
    Game id1, name 'Foo', has release year 2025.
    Game id2, same name 'Foo', has release year null.
    Setting id1's release year to null must be blocked — two games with the
    same name and null year would break the !add_game duplicate guard.
    """
    game = make_game(id=1, name="Foo")
    game.release_year = 2025
    conflict = make_game(id=2, name="Foo")
    conflict.release_year = None

    with patch("tpbackend.cmds.set_game_release_year.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [game, conflict]
        result = cmd.execute(make_user(), "1 null")

    assert "Error" in result
    assert "null" in result
    game.save.assert_not_called()
