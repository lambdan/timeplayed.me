"""Tests for SearchGamesCommand (!search)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.search_games import SearchGamesCommand


@pytest.fixture
def cmd():
    return SearchGamesCommand()


def test_empty_query_returns_help(cmd, make_user):
    result = cmd.execute(make_user(), "")
    assert "No query provided" in result


def test_no_results(cmd, make_user):
    with patch("tpbackend.cmds.search_games.search_games", return_value=[]):
        result = cmd.execute(make_user(), "nonexistent")
    assert "No games found" in result


def test_results_listed(cmd, make_user, make_game):
    games = [make_game(1, "Zelda"), make_game(2, "Zelda II")]
    with patch("tpbackend.cmds.search_games.search_games", return_value=games):
        result = cmd.execute(make_user(), "zelda")
    assert "Zelda" in result
    assert "Zelda II" in result
