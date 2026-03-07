import datetime
import os
import sys
from unittest.mock import MagicMock, patch

# Set environment variables before importing any tpbackend modules
os.environ.setdefault("DB_NAME_TIMEPLAYED", "test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("ADMINS", "admin123")

# Mock modules with circular imports or external dependencies before they are
# pulled in transitively by the command modules we want to test.
sys.modules["tpbackend.bot"] = MagicMock()
sys.modules["tpbackend.api"] = MagicMock()

# Import utils first to break the circular dependency between
# tpbackend.utils and tpbackend.storage.storage_v2.
import tpbackend.utils  # noqa: E402
from tpbackend.storage import storage_v2  # noqa: E402
from tpbackend.storage.storage_v2 import (  # noqa: E402
    Activity,
    Game,
    LiveActivity,
    Platform,
    User,
)

from tpbackend.cmds.abort_manual import AbortManualCommand  # noqa: E402
from tpbackend.cmds.add_activity import AddActivityCommand  # noqa: E402
from tpbackend.cmds.add_game import AddGameCommand  # noqa: E402
from tpbackend.cmds.add_platform import AddPlatformCommand  # noqa: E402
from tpbackend.cmds.block_commands import BlockCommandsCommand  # noqa: E402
from tpbackend.cmds.delete_activity import DeleteActivityCommand  # noqa: E402
from tpbackend.cmds.delete_activity_admin import DeleteActivityAdminCommand  # noqa: E402
from tpbackend.cmds.emulated import ToggleEmulatedCommand  # noqa: E402
from tpbackend.cmds.get_activity import GetActivityCommand  # noqa: E402
from tpbackend.cmds.get_game import GetGameCommand  # noqa: E402
from tpbackend.cmds.help import HelpCommand  # noqa: E402
from tpbackend.cmds.last import LastActivityCommand  # noqa: E402
from tpbackend.cmds.list_platforms import ListPlatformsCommand  # noqa: E402
from tpbackend.cmds.search_games import SearchGamesCommand  # noqa: E402
from tpbackend.cmds.set_default_platform import SetDefaultPlatformCommand  # noqa: E402
from tpbackend.cmds.set_game import SetGameCommand  # noqa: E402
from tpbackend.cmds.set_game_admin import SetGameAdminCommand  # noqa: E402
from tpbackend.cmds.set_pc_platform import SetPCPlatformCommand  # noqa: E402
from tpbackend.cmds.set_platform import SetPlatformCommand  # noqa: E402
from tpbackend.cmds.start_manual import StartManualCommand  # noqa: E402
from tpbackend.cmds.stop_manual import StopManualCommand  # noqa: E402
from tpbackend.cmds.time_manual import TimeManualCommand  # noqa: E402

# TODO: Proper python test framework?

_FAILURES = 0


def fail(msg: str = ""):
    global _FAILURES
    _FAILURES += 1
    if msg:
        print(f"  ❌ {msg}")
    else:
        print("❌")


def check(condition: bool, description: str):
    print(f"  {description}", end="... ")
    if condition:
        print("✅")
    else:
        print("❌ FAILED")
        fail()


def assertIn(result: str, substr: str, description: str):
    check(substr in result, description)


def assertNotIn(result: str, substr: str, description: str):
    check(substr not in result, description)


def assertEqual(a, b, description: str):
    check(a == b, description)


# ---------------------------------------------------------------------------
# Helpers that build lightweight mock objects mimicking Peewee model instances
# ---------------------------------------------------------------------------

_TS = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
_STARTED = datetime.datetime(2025, 6, 1, 11, 0, 0, tzinfo=datetime.timezone.utc)


def make_platform(id=1, abbreviation="win", name="Windows") -> MagicMock:
    p = MagicMock(spec=Platform)
    p.id = id
    p.abbreviation = abbreviation
    p.name = name
    return p


def make_game(id=1, name="Test Game", aliases=None) -> MagicMock:
    g = MagicMock(spec=Game)
    g.id = id
    g.name = name
    g.aliases = aliases if aliases is not None else []
    return g


def make_user(
    id="user1",
    name="testuser",
    blocked=False,
    default_platform=None,
    pc_platform="win",
) -> MagicMock:
    u = MagicMock(spec=User)
    u.id = id
    u.name = name
    u.bot_commands_blocked = blocked
    u.pc_platform = pc_platform
    u.default_platform = default_platform or make_platform()
    return u


def make_admin_user() -> MagicMock:
    """Return a user whose id is in ADMINS."""
    return make_user(id="admin123", name="admin")


def make_activity(
    id=1,
    user=None,
    game=None,
    platform=None,
    seconds=3600,
    timestamp=None,
    emulated=False,
) -> MagicMock:
    a = MagicMock(spec=Activity)
    a.id = id
    # Peewee model __str__ returns the primary key value; replicate that here
    # so that f"#{act}" in last.py produces the expected string.
    a.__str__ = MagicMock(return_value=str(id))
    _user = user or make_user()
    _game = game or make_game()
    _platform = platform or make_platform()
    a.user = _user
    a.user_id = _user.id
    a.game = _game
    a.game_id = _game.id
    a.platform = _platform
    a.platform_id = _platform.id
    a.seconds = seconds
    a.timestamp = timestamp or _TS
    a.emulated = emulated
    return a


def make_live_activity(user=None, game=None, platform=None, started=None) -> MagicMock:
    la = MagicMock(spec=LiveActivity)
    la.user = user or make_user()
    la.game = game or make_game()
    la.platform = platform or make_platform()
    la.started = started or _STARTED
    return la


def make_activity_queryset(activities: list) -> MagicMock:
    """Return a mock that mimics a Peewee queryset chain ending in a list."""
    qs = MagicMock()
    qs.where.return_value = qs
    qs.order_by.return_value = qs
    qs.limit.return_value = activities
    qs.__iter__ = MagicMock(return_value=iter(activities))
    qs.__len__ = MagicMock(return_value=len(activities))
    return qs


# ===========================================================================
# SearchGamesCommand
# ===========================================================================

print("SearchGamesCommand")

cmd_search = SearchGamesCommand()
user = make_user()

result = cmd_search.execute(user, "")
assertIn(result, "No query provided", "empty query")

with patch("tpbackend.cmds.search_games.search_games", return_value=[]):
    result = cmd_search.execute(user, "nonexistent")
    assertIn(result, "No games found", "query with no results")

with patch(
    "tpbackend.cmds.search_games.search_games",
    return_value=[make_game(1, "Zelda"), make_game(2, "Zelda II")],
):
    result = cmd_search.execute(user, "zelda")
    assertIn(result, "Zelda", "query with results lists game names")
    assertIn(result, "Zelda II", "query with results lists all games")

# ===========================================================================
# GetGameCommand
# ===========================================================================

print("GetGameCommand")

cmd_gg = GetGameCommand()
user = make_user()

with patch.object(Game, "get_or_none", return_value=None):
    result = cmd_gg.execute(user, "999")
    assertIn(result, "Error", "game not found returns error")

with patch.object(Game, "get_or_none", return_value=make_game(1, "Metroid")):
    result = cmd_gg.execute(user, "1")
    assertIn(result, "Metroid", "found game shows name")
    assertNotIn(result, "Aliases", "game without aliases has no aliases section")

with patch.object(
    Game, "get_or_none", return_value=make_game(2, "Metroid", aliases=["Super Metroid"])
):
    result = cmd_gg.execute(user, "2")
    assertIn(result, "Metroid", "found game with alias shows name")
    assertIn(result, "Super Metroid", "alias appears in output")

# ===========================================================================
# GetActivityCommand
# ===========================================================================

print("GetActivityCommand")

cmd_ga = GetActivityCommand()
user = make_user()
platform = make_platform(1, "switch", "Nintendo Switch")
game = make_game(5, "Kirby")
activity = make_activity(42, user=user, game=game, platform=platform, seconds=7200)

with patch.object(Activity, "get_or_none", return_value=None):
    result = cmd_ga.execute(user, "999")
    assertIn(result, "Error", "activity not found returns error")

with patch.object(Activity, "get_or_none", return_value=activity):
    with patch.object(User, "get_or_none", return_value=user):
        with patch.object(Game, "get_or_none", return_value=game):
            with patch.object(Platform, "get_or_none", return_value=platform):
                result = cmd_ga.execute(user, "42")
                assertIn(result, "42", "activity id in output")
                assertIn(result, "Kirby", "game name in output")
                assertIn(result, "testuser", "user name in output")
                assertIn(result, "02:00:00", "duration formatted correctly")

# ===========================================================================
# LastActivityCommand
# ===========================================================================

print("LastActivityCommand")

cmd_last = LastActivityCommand()
user = make_user()

with patch.object(Activity, "select", return_value=make_activity_queryset([])):
    result = cmd_last.execute(user, "")
    assertIn(result, "No activities found", "no activities")

act1 = make_activity(10, user=user, game=make_game(1, "Mario"), seconds=1800)
act1.timestamp = datetime.datetime(2025, 6, 2, 12, 0, 0, tzinfo=datetime.timezone.utc)

with patch.object(Activity, "select", return_value=make_activity_queryset([act1])):
    result = cmd_last.execute(user, "")
    assertIn(result, "Mario", "game name in last activity")
    assertIn(result, "10", "activity id in last activity")

act2 = make_activity(11, user=user, game=make_game(2, "Luigi"), seconds=900)
act2.timestamp = datetime.datetime(2025, 6, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)

with patch.object(
    Activity, "select", return_value=make_activity_queryset([act1, act2])
):
    result = cmd_last.execute(user, "2")
    assertIn(result, "Mario", "multiple activities: first game")
    assertIn(result, "Luigi", "multiple activities: second game")

# ===========================================================================
# AddActivityCommand
# ===========================================================================

print("AddActivityCommand")

cmd_aa = AddActivityCommand()
user = make_user()

result = cmd_aa.execute(user, "onlyoneword")
assertIn(result, "Invalid syntax", "too few args returns invalid syntax")

with patch.object(Game, "get_or_none", return_value=None):
    with patch("tpbackend.cmds.add_activity.search_games", return_value=[]):
        result = cmd_aa.execute(user, "999 01:00:00")
        assertIn(result, "Error", "game not found")

with patch.object(Game, "get_or_none", return_value=make_game(1, "Castlevania")):
    result = cmd_aa.execute(user, "1 badformat")
    assertIn(result, "Error", "invalid duration format")

mock_api = sys.modules["tpbackend.api"]
mock_api.get_activities.return_value.total = 0

with patch.object(Game, "get_or_none", return_value=make_game(1, "Castlevania")):
    result = cmd_aa.execute(user, "1 17:00:00")
    assertIn(result, "Error", "duration too long")

with patch.object(Game, "get_or_none", return_value=make_game(1, "Castlevania")):
    with patch("tpbackend.cmds.add_activity.last_platform_for_game", return_value=None):
        with patch.object(Platform, "get_by_id", return_value=make_platform()):
            with patch("tpbackend.cmds.add_activity.add_session") as mock_add:
                saved = make_activity(1, seconds=3600)
                mock_add.return_value = (saved, None)
                result = cmd_aa.execute(user, "1 01:00:00")
                assertIn(result, "✅", "successful add returns confirmation")

# ===========================================================================
# DeleteActivityCommand
# ===========================================================================

print("DeleteActivityCommand")

cmd_del = DeleteActivityCommand()
user = make_user(id="user1")

with patch.object(Activity, "get_or_none", return_value=None):
    result = cmd_del.execute(user, "999")
    assertIn(result, "not found", "activity not found")

other_user = make_user(id="user2")
act_other = make_activity(5, user=other_user)
with patch.object(Activity, "get_or_none", return_value=act_other):
    result = cmd_del.execute(user, "5")
    assertIn(result, "Not your activity", "cannot delete another user's activity")

act_own = make_activity(6, user=user)
with patch.object(Activity, "get_or_none", return_value=act_own):
    result = cmd_del.execute(user, "6")
    assertIn(result, "deleted", "own activity deleted successfully")

# Multiple IDs
act_a = make_activity(7, user=user)
act_b = make_activity(8, user=user)
with patch.object(Activity, "get_or_none", side_effect=[act_a, act_b]):
    result = cmd_del.execute(user, "7,8")
    assertIn(result, "deleted", "multiple ids deleted")

# ===========================================================================
# StartManualCommand
# ===========================================================================

print("StartManualCommand")

cmd_start = StartManualCommand()
user = make_user()
game = make_game(3, "Hollow Knight")

with patch.object(Game, "get_or_none", return_value=None):
    result = cmd_start.execute(user, "999")
    assertIn(result, "Error", "game not found")

with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(LiveActivity, "get_or_none", return_value=make_live_activity()):
        result = cmd_start.execute(user, "3")
        assertIn(result, "already have a manual activity running", "already running")

with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(LiveActivity, "get_or_none", return_value=None):
        with patch("tpbackend.cmds.start_manual.last_platform_for_game", return_value=None):
            with patch.object(LiveActivity, "create"):
                result = cmd_start.execute(user, "3")
                assertIn(result, "Hollow Knight", "started activity shows game name")
                assertIn(result, "stop", "started activity mentions stop command")

# ===========================================================================
# StopManualCommand
# ===========================================================================

print("StopManualCommand")

cmd_stop = StopManualCommand()
user = make_user()

with patch.object(LiveActivity, "get_or_none", return_value=None):
    result = cmd_stop.execute(user, "")
    assertIn(result, "haven't started", "no live activity")

live = make_live_activity(user=user, game=make_game(1, "Ori"))
with patch.object(LiveActivity, "get_or_none", return_value=live):
    with patch("tpbackend.cmds.stop_manual.operations") as mock_ops:
        saved = make_activity(1, seconds=3600, game=make_game(1, "Ori"))
        mock_ops.add_session.return_value = (saved, None)
        result = cmd_stop.execute(user, "")
        assertIn(result, "✅", "stop saves activity")
        assertIn(result, "Ori", "stop shows game name")

live_short = make_live_activity(user=user, game=make_game(1, "Ori"))
with patch.object(LiveActivity, "get_or_none", return_value=live_short):
    with patch("tpbackend.cmds.stop_manual.operations") as mock_ops:
        mock_ops.add_session.return_value = (None, ValueError("too short"))
        result = cmd_stop.execute(user, "")
        assertIn(result, "too short", "very short session not saved")

# ===========================================================================
# AbortManualCommand
# ===========================================================================

print("AbortManualCommand")

cmd_abort = AbortManualCommand()
user = make_user()

with patch.object(LiveActivity, "get_or_none", return_value=None):
    result = cmd_abort.execute(user, "")
    assertIn(result, "no manual activity running", "no live activity to abort")

live = make_live_activity(user=user, game=make_game(1, "Bloodborne"))
with patch.object(LiveActivity, "get_or_none", return_value=live):
    result = cmd_abort.execute(user, "")
    assertIn(result, "Bloodborne", "abort shows game name")

# ===========================================================================
# TimeManualCommand
# ===========================================================================

print("TimeManualCommand")

cmd_time = TimeManualCommand()
user = make_user()

with patch.object(LiveActivity, "get_or_none", return_value=None):
    result = cmd_time.execute(user, "")
    assertIn(result, "no manual activity running", "no live activity")

started = tpbackend.utils.now() - datetime.timedelta(hours=1)
live = make_live_activity(
    user=user, game=make_game(1, "Elden Ring"), started=started
)
with patch.object(LiveActivity, "get_or_none", return_value=live):
    result = cmd_time.execute(user, "")
    assertIn(result, "Elden Ring", "time shows game name")
    assertIn(result, "01:", "time shows approximately 1 hour elapsed")

# ===========================================================================
# SetDefaultPlatformCommand
# ===========================================================================

print("SetDefaultPlatformCommand")

cmd_sdp = SetDefaultPlatformCommand()
platform_win = make_platform(1, "win", "Windows")
user = make_user(default_platform=platform_win)

result = cmd_sdp.execute(user, "")
assertIn(result, "win", "get current default platform")

with patch.object(Platform, "get_or_none", return_value=None):
    result = cmd_sdp.execute(user, "999")
    assertIn(result, "Error", "platform not found")

platform_ps5 = make_platform(2, "ps5", "PlayStation 5")
with patch.object(Platform, "get_or_none", return_value=platform_ps5):
    result = cmd_sdp.execute(user, "2")
    assertIn(result, "ps5", "default platform updated")

# ===========================================================================
# SetPCPlatformCommand
# ===========================================================================

print("SetPCPlatformCommand")

cmd_pcp = SetPCPlatformCommand()
user = make_user(pc_platform="win")

result = cmd_pcp.execute(user, "")
assertIn(result, "win", "get current pc platform")

result = cmd_pcp.execute(user, "invalid_os")
assertIn(result, "Invalid", "invalid OS rejected")

result = cmd_pcp.execute(user, "mac")
assertIn(result, "mac", "pc platform updated to mac")

result = cmd_pcp.execute(user, "linux")
assertIn(result, "linux", "pc platform updated to linux")

# ===========================================================================
# ListPlatformsCommand
# ===========================================================================

print("ListPlatformsCommand")

cmd_lp = ListPlatformsCommand()
user = make_user()

with patch("tpbackend.cmds.list_platforms.search_platforms", return_value=[]):
    result = cmd_lp.execute(user, "")
    assertIn(result, "No platforms found", "no platforms")

with patch(
    "tpbackend.cmds.list_platforms.search_platforms",
    return_value=[
        make_platform(1, "win", "Windows"),
        make_platform(2, "ps5", "PlayStation 5"),
    ],
):
    result = cmd_lp.execute(user, "")
    assertIn(result, "win", "platform abbreviation in list")
    assertIn(result, "ps5", "second platform in list")

# ===========================================================================
# SetGameCommand
# ===========================================================================

print("SetGameCommand")

cmd_sg = SetGameCommand()
user = make_user(id="user1")

result = cmd_sg.execute(user, "badargs")
assertIn(result, "Invalid syntax", "too few args")

with patch.object(Game, "get_or_none", return_value=None):
    result = cmd_sg.execute(user, "1 999")
    assertIn(result, "Error", "game not found")

game = make_game(2, "Donkey Kong")
with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd_sg.execute(user, "999 2")
        assertIn(result, "not found", "activity not found")

act = make_activity(10, user=make_user(id="user2"))
with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd_sg.execute(user, "10 2")
        assertIn(result, "not yours", "cannot change another user's activity")

act_own = make_activity(11, user=user, game=make_game(1, "Old Game"))
with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(Activity, "get_or_none", return_value=act_own):
        result = cmd_sg.execute(user, "11 2")
        assertIn(result, "Donkey Kong", "game changed successfully")

# ===========================================================================
# SetPlatformCommand
# ===========================================================================

print("SetPlatformCommand")

cmd_sp = SetPlatformCommand()
user = make_user(id="user1")

result = cmd_sp.execute(user, "onlyoneword")
assertIn(result, "Invalid syntax", "too few args")

with patch.object(Platform, "get_or_none", return_value=None):
    result = cmd_sp.execute(user, "1 999")
    assertIn(result, "Error", "platform not found")

platform_snes = make_platform(3, "snes", "Super NES")
with patch.object(Platform, "get_or_none", return_value=platform_snes):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd_sp.execute(user, "999 3")
        assertIn(result, "not found", "activity not found")

act_other = make_activity(20, user=make_user(id="user2"))
with patch.object(Platform, "get_or_none", return_value=platform_snes):
    with patch.object(Activity, "get_or_none", return_value=act_other):
        result = cmd_sp.execute(user, "20 3")
        assertIn(result, "not yours", "cannot change another user's activity")

act_own = make_activity(21, user=user, platform=make_platform(1, "win"))
act_own.platform.abbreviation = "win"
with patch.object(Platform, "get_or_none", return_value=platform_snes):
    with patch.object(Activity, "get_or_none", return_value=act_own):
        result = cmd_sp.execute(user, "21 3")
        assertIn(result, "snes", "platform changed successfully")

# ===========================================================================
# ToggleEmulatedCommand
# ===========================================================================

print("ToggleEmulatedCommand")

cmd_emu = ToggleEmulatedCommand()
user = make_user(id="user1")

with patch.object(Activity, "get_or_none", return_value=None):
    result = cmd_emu.execute(user, "999")
    assertIn(result, "Error", "activity not found")

act_other = make_activity(30, user=make_user(id="user2"))
with patch.object(Activity, "get_or_none", return_value=act_other):
    result = cmd_emu.execute(user, "30")
    assertIn(result, "not your activity", "cannot change another user's activity")

act_own = make_activity(31, user=user, emulated=False)
with patch.object(Activity, "get_or_none", return_value=act_own):
    result = cmd_emu.execute(user, "31")
    assertIn(result, "True", "emulated toggled to True")

act_own_emu = make_activity(32, user=user, emulated=True)
with patch.object(Activity, "get_or_none", return_value=act_own_emu):
    result = cmd_emu.execute(user, "32")
    assertIn(result, "False", "emulated toggled to False")

# ===========================================================================
# AddGameCommand
# ===========================================================================

print("AddGameCommand")

cmd_ag = AddGameCommand()
regular_user = make_user(id="user1")
admin_user = make_admin_user()

mock_api = sys.modules["tpbackend.api"]

# Regular user with no activity is not allowed
mock_api.get_oldest_activity.return_value = None
result = cmd_ag.execute(regular_user, "New Game")
assertIn(result, "not allowed", "new user without activity is not allowed")

# Regular user with recent activity is not allowed
one_hour_ago_ts_ms = int((tpbackend.utils.now().timestamp() - 3600) * 1000)  # 1h ago in ms
mock_oldest = MagicMock()
mock_oldest.timestamp = one_hour_ago_ts_ms
mock_api.get_oldest_activity.return_value = mock_oldest
result = cmd_ag.execute(regular_user, "New Game")
assertIn(result, "not allowed", "user with recent activity is not allowed")

# Admin is always allowed - empty name
result = cmd_ag.execute(admin_user, "")
assertIn(result, "No game name provided", "admin with empty name")

# Admin: game already exists
with patch("tpbackend.cmds.add_game.get_game_by_name_or_alias") as mock_find:
    mock_find.return_value = make_game(1, "Existing Game")
    result = cmd_ag.execute(admin_user, "Existing Game")
    assertIn(result, "already exist", "duplicate game rejected")

# Admin: new game added
with patch("tpbackend.cmds.add_game.get_game_by_name_or_alias", return_value=None):
    with patch(
        "tpbackend.cmds.add_game.get_game_by_name_or_alias_or_create",
        return_value=make_game(99, "Brand New Game"),
    ):
        result = cmd_ag.execute(admin_user, "Brand New Game")
        assertIn(result, "✅", "new game added")
        assertIn(result, "Brand New Game", "new game name in result")

# ===========================================================================
# HelpCommand
# ===========================================================================

print("HelpCommand")

cmd_help = HelpCommand()
regular_user = make_user()
admin_user = make_admin_user()

result = cmd_help.execute(regular_user, "")
assertIn(result, "!search", "help lists search command")
assertIn(result, "!last", "help lists last command")
assertNotIn(result, "admin", "non-admin help has no admin section")

result = cmd_help.execute(admin_user, "")
assertIn(result, "admin", "admin help shows admin notice")

result = cmd_help.execute(regular_user, "search")
assertIn(result, "search", "individual help for search command")

result = cmd_help.execute(regular_user, "nonexistent_cmd_xyz")
assertIn(result, "not found", "help for unknown command")

# ===========================================================================
# AddPlatformCommand  (admin)
# ===========================================================================

print("AddPlatformCommand")

cmd_ap = AddPlatformCommand()
admin_user = make_admin_user()

result = cmd_ap.execute(admin_user, "")
assertIn(result, "Error", "empty abbreviation rejected")

with patch.object(Platform, "get_or_none", return_value=make_platform(1, "win")):
    result = cmd_ap.execute(admin_user, "win")
    assertIn(result, "Error", "duplicate abbreviation rejected")

with patch.object(Platform, "get_or_none", return_value=None):
    new_platform = make_platform(10, "gamegear", None)
    with patch.object(Platform, "get_or_create", return_value=(new_platform, True)):
        result = cmd_ap.execute(admin_user, "gamegear")
        assertIn(result, "✅", "new platform added")
        assertIn(result, "gamegear", "new platform abbreviation in result")

# ===========================================================================
# DeleteActivityAdminCommand  (admin)
# ===========================================================================

print("DeleteActivityAdminCommand")

cmd_adm_del = DeleteActivityAdminCommand()
admin_user = make_admin_user()

with patch.object(Activity, "get_or_none", return_value=None):
    result = cmd_adm_del.execute(admin_user, "999")
    assertIn(result, "not found", "activity not found")

act = make_activity(50, user=make_user(id="user2"))
with patch.object(Activity, "get_or_none", return_value=act):
    result = cmd_adm_del.execute(admin_user, "50")
    assertIn(result, "deleted", "admin can delete any activity")

# Multiple IDs
act_x = make_activity(60, user=make_user(id="user2"))
act_y = make_activity(61, user=make_user(id="user3"))
with patch.object(Activity, "get_or_none", side_effect=[act_x, act_y]):
    result = cmd_adm_del.execute(admin_user, "60,61")
    assertIn(result, "deleted", "multiple activities deleted by admin")

# ===========================================================================
# SetGameAdminCommand  (admin)
# ===========================================================================

print("SetGameAdminCommand")

cmd_asg = SetGameAdminCommand()
admin_user = make_admin_user()

result = cmd_asg.execute(admin_user, "onlyoneword")
assertIn(result, "Invalid syntax", "too few args")

with patch.object(Game, "get_or_none", return_value=None):
    result = cmd_asg.execute(admin_user, "1 999")
    assertIn(result, "Error", "game not found")

game = make_game(2, "Tetris")
with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd_asg.execute(admin_user, "999 2")
        assertIn(result, "not found", "activity not found")

act = make_activity(70, user=make_user(id="another_user"), game=make_game(1, "Pong"))
with patch.object(Game, "get_or_none", return_value=game):
    with patch.object(Activity, "get_or_none", return_value=act):
        result = cmd_asg.execute(admin_user, "70 2")
        assertIn(result, "Tetris", "admin can change any user's activity game")

# ===========================================================================
# BlockCommandsCommand  (admin)
# ===========================================================================

print("BlockCommandsCommand")

cmd_block = BlockCommandsCommand()
admin_user = make_admin_user()

with patch.object(User, "get_or_none", return_value=None):
    result = cmd_block.execute(admin_user, "nonexistent_user")
    assertIn(result, "Error", "user not found")

target = make_user(id="victim", name="victim", blocked=False)
with patch.object(User, "get_or_none", return_value=target):
    result = cmd_block.execute(admin_user, "victim")
    assertIn(result, "victim", "status check shows user name")

with patch.object(User, "get_or_none", return_value=target):
    result = cmd_block.execute(admin_user, "victim on")
    assertIn(result, "True", "user blocked")

with patch.object(User, "get_or_none", return_value=target):
    result = cmd_block.execute(admin_user, "victim off")
    assertIn(result, "False", "user unblocked")

with patch.object(User, "get_or_none", return_value=target):
    result = cmd_block.execute(admin_user, "victim badarg")
    assertIn(result, "Invalid syntax", "invalid block argument")

# ===========================================================================
# Summary
# ===========================================================================

if _FAILURES > 0:
    print(f"\n{_FAILURES} test(s) failed ❌")
    sys.exit(1)

print("\nAll command tests passed! ✅")
sys.exit(0)
