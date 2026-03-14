from unittest.mock import MagicMock, patch

import pytest

from tpbackend.cmds.add_activity import AddActivityCommand
from tpbackend.permissions import PERMISSION_MANUAL_ACTIVITY

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def cmd():
    return AddActivityCommand()


# -----------------------------
# Permissions
# ----------------------------


def test_needs_permission(cmd, make_user):
    user = make_user()

    # users have manual activity permission by default, so this should work
    assert cmd.can_execute(user, "")

    # remove it
    user.remove_permission(PERMISSION_MANUAL_ACTIVITY)
    assert not cmd.can_execute(user, "")
