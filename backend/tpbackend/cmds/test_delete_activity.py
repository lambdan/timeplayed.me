"""Tests for DeleteActivityCommand (!delete)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.delete_activity import DeleteActivityCommand
from tpbackend.storage.storage_v2 import Activity


@pytest.fixture
def cmd():
    return DeleteActivityCommand()


def test_activity_not_found(cmd, make_user):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "999")
    assert "not found" in result


def test_cannot_delete_other_users_activity(cmd, make_user, make_activity):
    user = make_user(id="user1")
    other = make_user(id="user2")
    act = make_activity(5, user=other)

    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd.execute(user, "5")
    assert "Not your activity" in result


def test_own_activity_deleted(cmd, make_user, make_activity):
    user = make_user(id="user1")
    act = make_activity(6, user=user)

    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd.execute(user, "6")
    assert "deleted" in result


def test_multiple_ids(cmd, make_user, make_activity):
    user = make_user(id="user1")
    act_a = make_activity(7, user=user)
    act_b = make_activity(8, user=user)

    with patch.object(Activity, "get_or_none", side_effect=[act_a, act_b]):
        result = cmd.execute(user, "7,8")
    assert "deleted" in result
