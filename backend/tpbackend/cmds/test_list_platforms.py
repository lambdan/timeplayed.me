"""Tests for ListPlatformsCommand (!platforms)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.list_platforms import ListPlatformsCommand


@pytest.fixture
def cmd():
    return ListPlatformsCommand()


def test_no_platforms(cmd, make_user):
    with patch("tpbackend.cmds.list_platforms.search_platforms", return_value=[]):
        result = cmd.execute(make_user(), "")
    assert "No platforms found" in result


def test_platforms_listed(cmd, make_user, make_platform):
    platforms = [make_platform(1, "win", "Windows"), make_platform(2, "ps5", "PlayStation 5")]
    with patch("tpbackend.cmds.list_platforms.search_platforms", return_value=platforms):
        result = cmd.execute(make_user(), "")
    assert "win" in result
    assert "ps5" in result
