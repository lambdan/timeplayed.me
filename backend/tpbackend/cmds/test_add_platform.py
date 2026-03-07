"""Tests for AddPlatformCommand (!add_platform) — admin only."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.add_platform import AddPlatformCommand
from tpbackend.storage.storage_v2 import Platform


@pytest.fixture
def cmd():
    return AddPlatformCommand()


def test_empty_abbreviation_rejected(cmd, make_admin_user):
    result = cmd.execute(make_admin_user(), "")
    assert "Error" in result


def test_duplicate_abbreviation_rejected(cmd, make_admin_user, make_platform):
    with patch.object(Platform, "get_or_none", return_value=make_platform(1, "win")):
        result = cmd.execute(make_admin_user(), "win")
    assert "Error" in result


def test_new_platform_added(cmd, make_admin_user, make_platform):
    new_p = make_platform(10, "gamegear", None)
    with patch.object(Platform, "get_or_none", return_value=None):
        with patch.object(Platform, "get_or_create", return_value=(new_p, True)):
            result = cmd.execute(make_admin_user(), "gamegear")
    assert "✅" in result
    assert "gamegear" in result
