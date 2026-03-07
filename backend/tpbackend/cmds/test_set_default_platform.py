"""Tests for SetDefaultPlatformCommand (!platform / !set_default_platform)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.set_default_platform import SetDefaultPlatformCommand
from tpbackend.storage.storage_v2 import Platform


@pytest.fixture
def cmd():
    return SetDefaultPlatformCommand()


def test_get_current_platform(cmd, make_user, make_platform):
    user = make_user(default_platform=make_platform(1, "win", "Windows"))
    result = cmd.execute(user, "")
    assert "win" in result


def test_platform_not_found(cmd, make_user):
    with patch.object(Platform, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "999")
    assert "Error" in result


def test_platform_updated(cmd, make_user, make_platform):
    ps5 = make_platform(2, "ps5", "PlayStation 5")
    with patch.object(Platform, "get_or_none", return_value=ps5):
        result = cmd.execute(make_user(), "2")
    assert "ps5" in result
