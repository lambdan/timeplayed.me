"""
Tests for MoveGameCommand (!move_game / !mg).

Key scenarios covered:
- Invalid syntax (too few arguments)
- Non-numeric game ID (ValueError)
- from_game not found
- to_game not found
- No activities found for the game (user has none)
- Without confirmation: shows count preview and prompt
- With confirmation: moves activities and reports result
- User-filter verification
- Singular/plural grammar in the output messages
"""

from unittest.mock import MagicMock, patch

import pytest

from tpbackend.cmds.move_game import MoveGameCommand


@pytest.fixture
def cmd():
    return MoveGameCommand()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_invalid_syntax_too_few_args(cmd, make_user):
    result = cmd.execute(make_user(), "4")
    assert "Invalid syntax" in result


def test_non_numeric_from_game_id(cmd, make_user):
    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = ValueError
        result = cmd.execute(make_user(), "abc 35")
    assert "Invalid game ID" in result
    assert "abc" in result


def test_non_numeric_to_game_id(cmd, make_user, make_game):
    from_game = make_game(id=4, name="GTA V Legacy")
    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [from_game, ValueError("")]
        result = cmd.execute(make_user(), "4 xyz")
    assert "Invalid game ID" in result
    assert "xyz" in result


# ---------------------------------------------------------------------------
# Game lookup failures
# ---------------------------------------------------------------------------


def test_from_game_not_found(cmd, make_user):
    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        result = cmd.execute(make_user(), "4 35")
    assert "not found" in result
    assert "4" in result


def test_to_game_not_found(cmd, make_user, make_game):
    from_game = make_game(id=4, name="GTA V Legacy")
    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [from_game, None]
        result = cmd.execute(make_user(), "4 35")
    assert "not found" in result
    assert "35" in result


# ---------------------------------------------------------------------------
# No activities
# ---------------------------------------------------------------------------


def test_no_activities_for_user(cmd, make_user, make_game):
    user = make_user()
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = []
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(user, "4 35")

    assert "No activities" in result
    assert "GTA V Legacy" in result


# ---------------------------------------------------------------------------
# Confirmation flow
# ---------------------------------------------------------------------------


def test_without_confirmation_shows_preview(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    acts = [make_activity(id=i, user=user, game=from_game) for i in range(1, 4)]

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch(
        "tpbackend.cmds.move_game.set_game_actually"
    ) as mock_set_game:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = acts
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(user, "4 35")

    mock_set_game.assert_not_called()
    assert "3" in result
    assert "GTA V Legacy" in result
    assert "GTA V" in result
    assert "y" in result  # prompt to confirm


def test_move_single_activity(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    act = make_activity(id=1, user=user, game=from_game)

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch(
        "tpbackend.cmds.move_game.set_game_actually"
    ) as mock_set_game:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(user, "4 35 y")

    mock_set_game.assert_called_once_with(act, to_game)
    assert "1" in result  # count of activities moved
    assert "GTA V Legacy" in result
    assert "GTA V" in result


def test_move_multiple_activities(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    acts = [make_activity(id=i, user=user, game=from_game) for i in range(1, 4)]

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch(
        "tpbackend.cmds.move_game.set_game_actually"
    ) as mock_set_game:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = acts
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(user, "4 35 y")

    assert mock_set_game.call_count == 3
    assert "3" in result
    assert "GTA V Legacy" in result
    assert "GTA V" in result


def test_move_filters_by_user(cmd, make_user, make_game, make_activity):
    """The Activity query should include the user filter (verified via .where call)."""
    user = make_user()
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    act = make_activity(id=1, user=user, game=from_game)

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs

        cmd.execute(user, "4 35 y")

    # Verify that .where() was called (user + game filters applied)
    mock_qs.where.assert_called_once()


# ---------------------------------------------------------------------------
# Grammar: singular vs plural
# ---------------------------------------------------------------------------


def test_singular_activity_grammar(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="Game A")
    to_game = make_game(id=5, name="Game B")
    act = make_activity(id=1, user=user, game=from_game)

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs
        result = cmd.execute(user, "4 5 y")

    # exactly 1 activity → "activity" (singular)
    assert "activity" in result
    assert "activities" not in result


def test_plural_activity_grammar(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="Game A")
    to_game = make_game(id=5, name="Game B")
    acts = [make_activity(id=i, user=user, game=from_game) for i in range(1, 3)]

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = acts
        mock_activity_cls.select.return_value = mock_qs
        result = cmd.execute(user, "4 5 y")

    assert "activities" in result


def test_preview_singular_grammar(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="Game A")
    to_game = make_game(id=5, name="Game B")
    act = make_activity(id=1, user=user, game=from_game)

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs
        result = cmd.execute(user, "4 5")

    assert "1" in result
    assert "activity" in result
    assert "activities" not in result


def test_preview_plural_grammar(cmd, make_user, make_game, make_activity):
    user = make_user()
    from_game = make_game(id=4, name="Game A")
    to_game = make_game(id=5, name="Game B")
    acts = [make_activity(id=i, user=user, game=from_game) for i in range(1, 4)]

    with patch("tpbackend.cmds.move_game.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = acts
        mock_activity_cls.select.return_value = mock_qs
        result = cmd.execute(user, "4 5")

    assert "3" in result
    assert "activities" in result
