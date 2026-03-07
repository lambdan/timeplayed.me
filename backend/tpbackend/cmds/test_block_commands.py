"""Tests for BlockCommandsCommand (!block_commands) — admin only."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.block_commands import BlockCommandsCommand
from tpbackend.storage.storage_v2 import User


@pytest.fixture
def cmd():
    return BlockCommandsCommand()


def test_user_not_found(cmd, make_admin_user):
    with patch.object(User, "get_or_none", return_value=None):
        result = cmd.execute(make_admin_user(), "nonexistent_user")
    assert "Error" in result


def test_status_check(cmd, make_admin_user, make_user):
    target = make_user(id="victim", name="victim", blocked=False)
    with patch.object(User, "get_or_none", return_value=target):
        result = cmd.execute(make_admin_user(), "victim")
    assert "victim" in result


def test_block_user(cmd, make_admin_user, make_user):
    target = make_user(id="victim", name="victim", blocked=False)
    with patch.object(User, "get_or_none", return_value=target):
        result = cmd.execute(make_admin_user(), "victim on")
    assert "True" in result


def test_unblock_user(cmd, make_admin_user, make_user):
    target = make_user(id="victim", name="victim", blocked=True)
    with patch.object(User, "get_or_none", return_value=target):
        result = cmd.execute(make_admin_user(), "victim off")
    assert "False" in result


def test_invalid_block_argument(cmd, make_admin_user, make_user):
    target = make_user(id="victim", name="victim")
    with patch.object(User, "get_or_none", return_value=target):
        result = cmd.execute(make_admin_user(), "victim badarg")
    assert "Invalid syntax" in result
