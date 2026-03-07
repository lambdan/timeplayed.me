"""Tests for HelpCommand (!help)."""

import pytest

from tpbackend.cmds.help import HelpCommand


@pytest.fixture
def cmd():
    return HelpCommand()


def test_regular_user_sees_commands(cmd, make_user):
    result = cmd.execute(make_user(), "")
    assert "!search" in result
    assert "!last" in result


def test_regular_user_does_not_see_admin_notice(cmd, make_user):
    result = cmd.execute(make_user(), "")
    assert "admin" not in result


def test_admin_sees_admin_notice(cmd, make_admin_user):
    result = cmd.execute(make_admin_user(), "")
    assert "admin" in result


def test_individual_help_for_known_command(cmd, make_user):
    result = cmd.execute(make_user(), "search")
    assert "search" in result


def test_individual_help_for_unknown_command(cmd, make_user):
    result = cmd.execute(make_user(), "nonexistent_cmd_xyz")
    assert "not found" in result
