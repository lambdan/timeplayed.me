"""
Tests for SearchGamesCommand (!search).

This file is the canonical example for how to write a command test.
See TESTING.md for the full guide.

Key patterns used here:
- `cmd` fixture: creates the command object under test.
- `make_user` / `make_game` fixtures: factory functions from conftest.py that
  return lightweight MagicMock objects so no real database is needed.
- `patch(...)`: replaces a function/method for the duration of one test so the
  test controls what the production code "sees".  Always patch the name as it
  is *imported* in the module under test, not where it is defined.
- `result = cmd.execute(user, args)`: every command returns a plain string;
  just assert that the right substrings are (or are not) present.
"""

from unittest.mock import patch

import pytest

from tpbackend.cmds.search_games import SearchGamesCommand

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def cmd():
    """Return a fresh SearchGamesCommand for each test."""
    return SearchGamesCommand()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_empty_query_returns_help(cmd, make_user):
    result = cmd.execute(make_user(), "")
    assert "No query provided" in result


def test_no_results(cmd, make_user):
    # Patch the helper that hits the database so the test stays fast and
    # isolated.  The name to patch is the one *inside* the module being tested.
    with patch("tpbackend.cmds.search_games.search_games", return_value=[]):
        result = cmd.execute(make_user(), "nonexistent")
    assert "No games found" in result


def test_results_listed(cmd, make_user, make_game):
    games = [make_game(1, "Zelda"), make_game(2, "Zelda II")]
    with patch("tpbackend.cmds.search_games.search_games", return_value=games):
        result = cmd.execute(make_user(), "zelda")
    assert "Zelda" in result
    assert "Zelda II" in result


def test_results_show_year_when_set(cmd, make_user, make_game):
    games = [make_game(1, "Zelda", release_year=1986), make_game(2, "Zelda II", release_year=1987)]
    with patch("tpbackend.cmds.search_games.search_games", return_value=games):
        result = cmd.execute(make_user(), "zelda")
    assert "Zelda (1986)" in result
    assert "Zelda II (1987)" in result


def test_results_no_year_when_not_set(cmd, make_user, make_game):
    games = [make_game(1, "Zelda")]
    with patch("tpbackend.cmds.search_games.search_games", return_value=games):
        result = cmd.execute(make_user(), "zelda")
    assert "Zelda" in result
    assert "Zelda (" not in result
