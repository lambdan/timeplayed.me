"""Tests for ToggleEmulatedCommand (!emulated)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.emulated import ToggleEmulatedCommand
from tpbackend.storage.storage_v2 import Activity


@pytest.fixture
def cmd():
    return ToggleEmulatedCommand()


def test_activity_not_found(cmd, make_user):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd.execute(make_user(id="user1"), "999")
    assert "Error" in result


def test_cannot_toggle_other_users_activity(cmd, make_user, make_activity):
    user = make_user(id="user1")
    act = make_activity(30, user=make_user(id="user2"))

    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd.execute(user, "30")
    assert "not your activity" in result


def test_toggle_to_true(cmd, make_user, make_activity):
    user = make_user(id="user1")
    act = make_activity(31, user=user, emulated=False)

    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd.execute(user, "31")
    assert "True" in result


def test_toggle_to_false(cmd, make_user, make_activity):
    user = make_user(id="user1")
    act = make_activity(32, user=user, emulated=True)

    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd.execute(user, "32")
    assert "False" in result
