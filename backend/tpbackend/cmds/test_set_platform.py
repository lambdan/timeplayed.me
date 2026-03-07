"""Tests for SetPlatformCommand (!set_platform)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.set_platform import SetPlatformCommand
from tpbackend.storage.storage_v2 import Activity, Platform


@pytest.fixture
def cmd():
    return SetPlatformCommand()


def test_too_few_args(cmd, make_user):
    result = cmd.execute(make_user(id="user1"), "onlyoneword")
    assert "Invalid syntax" in result


def test_platform_not_found(cmd, make_user):
    with patch.object(Platform, "get_or_none", return_value=None):
        result = cmd.execute(make_user(id="user1"), "1 999")
    assert "Error" in result


def test_activity_not_found(cmd, make_user, make_platform):
    snes = make_platform(3, "snes", "Super NES")
    with patch.object(Platform, "get_or_none", return_value=snes):
        with patch.object(Activity, "get_or_none", return_value=None):
            result = cmd.execute(make_user(id="user1"), "999 3")
    assert "not found" in result


def test_cannot_change_other_users_activity(cmd, make_user, make_platform, make_activity):
    user = make_user(id="user1")
    snes = make_platform(3, "snes", "Super NES")
    act = make_activity(20, user=make_user(id="user2"))

    with patch.object(Platform, "get_or_none", return_value=snes):
        with patch.object(Activity, "get_or_none", return_value=act):
            result = cmd.execute(user, "20 3")
    assert "not yours" in result


def test_platform_changed_successfully(cmd, make_user, make_platform, make_activity):
    user = make_user(id="user1")
    snes = make_platform(3, "snes", "Super NES")
    act = make_activity(21, user=user, platform=make_platform(1, "win"))
    act.platform.abbreviation = "win"

    with patch.object(Platform, "get_or_none", return_value=snes):
        with patch.object(Activity, "get_or_none", return_value=act):
            result = cmd.execute(user, "21 3")
    assert "snes" in result
