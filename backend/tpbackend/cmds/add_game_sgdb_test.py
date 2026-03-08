"""
Tests for AddGameSGDBCommand (!add_sgdb).

Key scenarios covered:
- Input validation (empty, non-numeric, zero/negative)
- SGDB ID already in DB
- Game not found on SGDB / no name on SGDB
- No name collision → game added successfully
- Name collision: SGDB has no release year → hard error
- Name collision: existing game has no release year → hard error with hint
- Name collision: same name AND same release year → hard error (true duplicate)
- Name collision: same name, different release years → allowed (both years set)
"""

from unittest.mock import MagicMock, patch, call

import pytest

from tpbackend.cmds.add_game_sgdb import AddGameSGDBCommand

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def cmd():
    return AddGameSGDBCommand()


def _mock_sgdb_game(name: str, release_year: int | None):
    """Build a minimal mock resembling a steamgrid.Game object."""
    g = MagicMock()
    g.name = name
    if release_year is not None:
        g.release_date = MagicMock()
        g.release_date.year = release_year
    else:
        g.release_date = None
    return g


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_empty_input(cmd, make_user):
    result = cmd.execute(make_user(), "")
    assert "No SteamGridDB ID provided" in result


def test_non_numeric_input(cmd, make_user):
    result = cmd.execute(make_user(), "abc")
    assert "Invalid id" in result


def test_zero_id(cmd, make_user):
    result = cmd.execute(make_user(), "0")
    assert "Invalid id" in result


def test_negative_id(cmd, make_user):
    result = cmd.execute(make_user(), "-5")
    assert "Invalid id" in result


# ---------------------------------------------------------------------------
# SGDB ID already in DB
# ---------------------------------------------------------------------------


def test_sgdb_id_already_in_db(cmd, make_user, make_game):
    existing = make_game(id=21, name="Resident Evil 4")
    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = existing
        result = cmd.execute(make_user(), "3168")
    assert "Error" in result
    assert "SteamGridDB ID" in result
    assert "3168" in result


# ---------------------------------------------------------------------------
# SGDB API errors
# ---------------------------------------------------------------------------


def test_game_not_found_on_sgdb(cmd, make_user):
    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id",
            return_value=None,
        ):
            result = cmd.execute(make_user(), "9999")
    assert "did not find game on SGDB" in result


def test_sgdb_game_has_no_name(cmd, make_user):
    g = MagicMock()
    g.name = None
    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id", return_value=g
        ):
            result = cmd.execute(make_user(), "9999")
    assert "no name" in result


# ---------------------------------------------------------------------------
# Happy path — no name collision
# ---------------------------------------------------------------------------


def test_successful_add_no_collision(cmd, make_user):
    new_game_mock = MagicMock()
    new_game_mock.name = "Half-Life"
    new_game_mock.id = 7
    new_game_mock.sgdb_id = 35291

    sgdb_game = _mock_sgdb_game("Half-Life", release_year=1998)

    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None  # no SGDB ID collision
        mock_game_cls.create.return_value = new_game_mock
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id",
            return_value=sgdb_game,
        ):
            with patch(
                "tpbackend.cmds.add_game_sgdb.get_game_by_name_or_alias",
                return_value=None,  # no name collision
            ):
                result = cmd.execute(make_user(), "35291")

    assert "✅" in result
    assert "Half-Life" in result
    mock_game_cls.create.assert_called_once_with(
        name="Half-Life", sgdb_id=35291, release_year=1998
    )


# ---------------------------------------------------------------------------
# Name collision: SGDB reports no release year → hard error
# ---------------------------------------------------------------------------


def test_name_collision_sgdb_has_no_year(cmd, make_user, make_game):
    existing = make_game(id=21, name="Some Game")
    existing.release_year = 2000
    sgdb_game = _mock_sgdb_game("Some Game", release_year=None)

    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id",
            return_value=sgdb_game,
        ):
            with patch(
                "tpbackend.cmds.add_game_sgdb.get_game_by_name_or_alias",
                return_value=existing,
            ):
                result = cmd.execute(make_user(), "1234")

    assert "Error" in result
    assert "no release year" in result
    mock_game_cls.create.assert_not_called()


# ---------------------------------------------------------------------------
# Name collision: existing game has no release year → hard error with hint
# ---------------------------------------------------------------------------


def test_name_collision_existing_has_no_year(cmd, make_user, make_game):
    existing = make_game(id=21, name="Resident Evil 4")
    existing.release_year = None  # existing game has no year set
    sgdb_game = _mock_sgdb_game("Resident Evil 4", release_year=2023)

    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id",
            return_value=sgdb_game,
        ):
            with patch(
                "tpbackend.cmds.add_game_sgdb.get_game_by_name_or_alias",
                return_value=existing,
            ):
                result = cmd.execute(make_user(), "5332120")

    assert "Error" in result
    assert "no release year" in result
    # Should include a hint referencing the existing game id
    assert "21" in result
    mock_game_cls.create.assert_not_called()


# ---------------------------------------------------------------------------
# Name collision: same name AND same year → true duplicate error
# ---------------------------------------------------------------------------


def test_name_collision_same_year_is_duplicate(cmd, make_user, make_game):
    existing = make_game(id=21, name="Resident Evil 4")
    existing.release_year = 2023
    sgdb_game = _mock_sgdb_game("Resident Evil 4", release_year=2023)

    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [
            None,  # first call: SGDB ID check
            existing,  # second call: true-duplicate check (name + year) — finds the same row
        ]
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id",
            return_value=sgdb_game,
        ):
            with patch(
                "tpbackend.cmds.add_game_sgdb.get_game_by_name_or_alias",
                return_value=existing,
            ):
                result = cmd.execute(make_user(), "5332120")

    assert "Error" in result
    assert "already exists" in result
    mock_game_cls.create.assert_not_called()


# ---------------------------------------------------------------------------
# Name collision: same name, different release years → allowed
# ---------------------------------------------------------------------------


def test_name_collision_different_years_allowed(cmd, make_user, make_game):
    """
    'Resident Evil 4' (2005) already in DB.
    Adding SGDB 5332120 ('Resident Evil 4', year 2023) should succeed because
    both games have distinct release years.
    """
    existing = make_game(id=21, name="Resident Evil 4")
    existing.release_year = 2005

    new_game_mock = MagicMock()
    new_game_mock.name = "Resident Evil 4"
    new_game_mock.id = 99
    new_game_mock.sgdb_id = 5332120

    sgdb_game = _mock_sgdb_game("Resident Evil 4", release_year=2023)

    with patch("tpbackend.cmds.add_game_sgdb.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [
            None,  # first call: SGDB ID check — not in DB
            None,  # second call: true-duplicate check (name=RE4, year=2023) — not found
        ]
        mock_game_cls.create.return_value = new_game_mock
        with patch(
            "tpbackend.cmds.add_game_sgdb.steamgriddb.get_game_by_id",
            return_value=sgdb_game,
        ):
            with patch(
                "tpbackend.cmds.add_game_sgdb.get_game_by_name_or_alias",
                return_value=existing,
            ):
                result = cmd.execute(make_user(), "5332120")

    assert "✅" in result
    assert "Resident Evil 4" in result
    mock_game_cls.create.assert_called_once_with(
        name="Resident Evil 4", sgdb_id=5332120, release_year=2023
    )
