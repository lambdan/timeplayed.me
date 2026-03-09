"""
Tests for MoveGameAdminCommand (!adm_move_game / !amg).

Key scenarios covered:
- Invalid syntax (wrong number of arguments)
- Non-numeric game ID (ValueError)
- from_game not found
- to_game not found
- No activities found (no activities for that game across all users)
- Successfully moving activities across all users
"""

from unittest.mock import MagicMock, patch

import pytest

from tpbackend.cmds.move_game_admin import MoveGameAdminCommand


@pytest.fixture
def cmd():
    return MoveGameAdminCommand()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_invalid_syntax_too_few_args(cmd, make_admin_user):
    result = cmd.execute(make_admin_user(), "4")
    assert "Invalid syntax" in result


def test_invalid_syntax_too_many_args(cmd, make_admin_user):
    result = cmd.execute(make_admin_user(), "4 35 extra")
    assert "Invalid syntax" in result


def test_non_numeric_from_game_id(cmd, make_admin_user):
    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = ValueError
        result = cmd.execute(make_admin_user(), "abc 35")
    assert "Invalid game ID" in result
    assert "abc" in result


def test_non_numeric_to_game_id(cmd, make_admin_user, make_game):
    from_game = make_game(id=4, name="GTA V Legacy")
    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [from_game, ValueError("")]
        result = cmd.execute(make_admin_user(), "4 xyz")
    assert "Invalid game ID" in result
    assert "xyz" in result


# ---------------------------------------------------------------------------
# Game lookup failures
# ---------------------------------------------------------------------------


def test_from_game_not_found(cmd, make_admin_user):
    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.return_value = None
        result = cmd.execute(make_admin_user(), "4 35")
    assert "not found" in result
    assert "4" in result


def test_to_game_not_found(cmd, make_admin_user, make_game):
    from_game = make_game(id=4, name="GTA V Legacy")
    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls:
        mock_game_cls.get_or_none.side_effect = [from_game, None]
        result = cmd.execute(make_admin_user(), "4 35")
    assert "not found" in result
    assert "35" in result


# ---------------------------------------------------------------------------
# No activities
# ---------------------------------------------------------------------------


def test_no_activities_across_all_users(cmd, make_admin_user, make_game):
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")

    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game_admin.Activity"
    ) as mock_activity_cls:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = []
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(make_admin_user(), "4 35")

    assert "No activities" in result
    assert "GTA V Legacy" in result


# ---------------------------------------------------------------------------
# Successful move
# ---------------------------------------------------------------------------


def test_move_single_activity_all_users(
    cmd, make_admin_user, make_user, make_game, make_activity
):
    admin = make_admin_user()
    other_user = make_user(id="user2")
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    act = make_activity(id=1, user=other_user, game=from_game)

    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game_admin.Activity"
    ) as mock_activity_cls, patch(
        "tpbackend.cmds.move_game_admin.set_game_actually"
    ) as mock_set_game:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(admin, "4 35")

    mock_set_game.assert_called_once_with(act, to_game)
    assert "1" in result
    assert "GTA V Legacy" in result
    assert "GTA V" in result


def test_move_multiple_activities_all_users(
    cmd, make_admin_user, make_user, make_game, make_activity
):
    admin = make_admin_user()
    users = [make_user(id=f"user{i}") for i in range(3)]
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    acts = [make_activity(id=i + 1, user=users[i], game=from_game) for i in range(3)]

    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game_admin.Activity"
    ) as mock_activity_cls, patch(
        "tpbackend.cmds.move_game_admin.set_game_actually"
    ) as mock_set_game:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = acts
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(admin, "4 35")

    assert mock_set_game.call_count == 3
    assert "3" in result
    assert "GTA V Legacy" in result
    assert "GTA V" in result


def test_move_does_not_filter_by_user(
    cmd, make_admin_user, make_user, make_game, make_activity
):
    """Admin command must NOT include a user filter — it operates on all users."""
    admin = make_admin_user()
    from_game = make_game(id=4, name="GTA V Legacy")
    to_game = make_game(id=35, name="GTA V")
    act = make_activity(id=1, user=make_user(id="someone_else"), game=from_game)

    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game_admin.Activity"
    ) as mock_activity_cls, patch(
        "tpbackend.cmds.move_game_admin.set_game_actually"
    ) as mock_set_game:
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs

        result = cmd.execute(admin, "4 35")

    # Activity belonging to another user was still moved
    mock_set_game.assert_called_once_with(act, to_game)
    assert "1" in result


# ---------------------------------------------------------------------------
# Grammar: singular vs plural
# ---------------------------------------------------------------------------


def test_singular_activity_grammar(cmd, make_admin_user, make_game, make_activity):
    from_game = make_game(id=4, name="Game A")
    to_game = make_game(id=5, name="Game B")
    act = make_activity(id=1, game=from_game)

    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game_admin.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game_admin.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = [act]
        mock_activity_cls.select.return_value = mock_qs
        result = cmd.execute(make_admin_user(), "4 5")

    assert "activity" in result
    assert "activities" not in result


def test_plural_activity_grammar(cmd, make_admin_user, make_game, make_activity):
    from_game = make_game(id=4, name="Game A")
    to_game = make_game(id=5, name="Game B")
    acts = [make_activity(id=i, game=from_game) for i in range(1, 4)]

    with patch("tpbackend.cmds.move_game_admin.Game") as mock_game_cls, patch(
        "tpbackend.cmds.move_game_admin.Activity"
    ) as mock_activity_cls, patch("tpbackend.cmds.move_game_admin.set_game_actually"):
        mock_game_cls.get_or_none.side_effect = [from_game, to_game]
        mock_qs = MagicMock()
        mock_qs.where.return_value = acts
        mock_activity_cls.select.return_value = mock_qs
        result = cmd.execute(make_admin_user(), "4 5")

    assert "activities" in result
