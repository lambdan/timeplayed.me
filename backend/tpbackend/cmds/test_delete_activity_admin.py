"""Tests for DeleteActivityAdminCommand (!adm_delete) — admin only."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.delete_activity_admin import DeleteActivityAdminCommand
from tpbackend.storage.storage_v2 import Activity


@pytest.fixture
def cmd():
    return DeleteActivityAdminCommand()


def test_activity_not_found(cmd, make_admin_user):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd.execute(make_admin_user(), "999")
    assert "not found" in result


def test_admin_can_delete_any_activity(cmd, make_admin_user, make_user, make_activity):
    act = make_activity(50, user=make_user(id="user2"))
    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd.execute(make_admin_user(), "50")
    assert "deleted" in result


def test_multiple_ids(cmd, make_admin_user, make_user, make_activity):
    act_x = make_activity(60, user=make_user(id="user2"))
    act_y = make_activity(61, user=make_user(id="user3"))
    with patch.object(Activity, "get_or_none", side_effect=[act_x, act_y]):
        result = cmd.execute(make_admin_user(), "60,61")
    assert "deleted" in result
