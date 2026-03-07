"""Tests for LastActivityCommand (!last)."""

import datetime
from unittest.mock import patch

import pytest

from tpbackend.cmds.last import LastActivityCommand
from tpbackend.storage.storage_v2 import Activity


@pytest.fixture
def cmd():
    return LastActivityCommand()


def test_no_activities(cmd, make_user, make_activity_queryset):
    with patch.object(Activity, "select", return_value=make_activity_queryset([])):
        result = cmd.execute(make_user(), "")
    assert "No activities found" in result


def test_single_activity_shows_game_and_id(cmd, make_user, make_game, make_activity, make_activity_queryset):
    user = make_user()
    act = make_activity(10, user=user, game=make_game(1, "Mario"), seconds=1800)
    act.timestamp = datetime.datetime(2025, 6, 2, 12, 0, 0, tzinfo=datetime.timezone.utc)

    with patch.object(Activity, "select", return_value=make_activity_queryset([act])):
        result = cmd.execute(user, "")

    assert "Mario" in result
    assert "10" in result


def test_multiple_activities(cmd, make_user, make_game, make_activity, make_activity_queryset):
    user = make_user()
    act1 = make_activity(10, user=user, game=make_game(1, "Mario"), seconds=1800)
    act1.timestamp = datetime.datetime(2025, 6, 2, 12, 0, 0, tzinfo=datetime.timezone.utc)
    act2 = make_activity(11, user=user, game=make_game(2, "Luigi"), seconds=900)
    act2.timestamp = datetime.datetime(2025, 6, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)

    with patch.object(Activity, "select", return_value=make_activity_queryset([act1, act2])):
        result = cmd.execute(user, "2")

    assert "Mario" in result
    assert "Luigi" in result
