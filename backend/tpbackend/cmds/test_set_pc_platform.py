"""Tests for SetPCPlatformCommand (!pcplatform / !pcp)."""

import pytest

from tpbackend.cmds.set_pc_platform import SetPCPlatformCommand


@pytest.fixture
def cmd():
    return SetPCPlatformCommand()


def test_get_current_pc_platform(cmd, make_user):
    result = cmd.execute(make_user(pc_platform="win"), "")
    assert "win" in result


def test_invalid_os_rejected(cmd, make_user):
    result = cmd.execute(make_user(), "invalid_os")
    assert "Invalid" in result


@pytest.mark.parametrize("os_name", ["mac", "linux", "win"])
def test_valid_os_accepted(cmd, make_user, os_name):
    result = cmd.execute(make_user(), os_name)
    assert os_name in result
