from .commands.add_activity import AddActivityCommand
from .commands.add_game_sgdb import AddGameSGDBCommand
from .commands.add_game_admin import AddGameAdminCommand
from .commands.add_platform import AddPlatformCommand
from .commands.delete_activity import DeleteActivityCommand
from .commands.delete_game import DeleteGameCommand
from .commands.delete_platform import DeletePlatformCommand
from .commands.emulated import ToggleEmulatedCommand
from .commands.get_activity import GetActivityCommand
from .commands.get_cache_stats import GetCacheStats
from .commands.get_game import GetGameCommand
from .commands.last import LastActivityCommand
from .commands.permission_add import AddPermissionCommand
from .commands.permission_remove import RemovePermissionCommand
from .commands.refresh_search import RefreshSearch
from .commands.search_games import SearchGamesCommand
from .commands.set_default_platform import SetDefaultPlatformCommand
from .commands.set_game import SetGameCommand
from .commands.set_game_image import SetGameImageCommand
from .commands.igdb_missing_admin import MissingIGDBAdminCommand
from .commands.igdb_set_id import SetIGDBIDCommand
from .commands.igdb_add_game import AddGameIGDBCommand
from .commands.igdb_auto import AutoIGDBAdminCommand
from .commands.set_pc_platform import SetPCPlatformCommand
from .commands.set_platform import SetPlatformCommand
from .commands.set_platform_name import SetPlatformNameCommand
from .commands.set_sgdb_id import SetSGDBIDCommand
from .commands.start_manual import StartManualCommand
from .commands.stop_manual import StopManualCommand
from .commands.list_platforms import ListPlatformsCommand
from .commands.set_steam_id import SetSteamIDCommand
from .commands.set_sgdb_grid_id import SetSGDBGridIDCommand
from .commands.add_game_alias import AddGameAliasCommand
from .commands.delete_game_alias import DeleteGameAliasCommand
from .commands.set_game_release_year import SetGameReleaseYearCommand
from .commands.search_users import SearchUsersCommand
from .commands.uptime import UptimeCommand
from .commands.set_game_admin import SetGameAdminCommand
from .commands.delete_activity_admin import DeleteActivityAdminCommand
from .commands.abort_manual import AbortManualCommand
from .commands.time_manual import TimeManualCommand
from .commands.missing_sgdb_admin import MissingSGDBAdminCommand
from .commands.search_sgdb import SearchSGDBCommand
from .commands.auto_sgdb import AutoSGDBAdminCommand
from .commands.games_without_activity_admin import GamesWithoutActivityAdminCommand
from .commands.move_game import MoveGameCommand
from .commands.move_game_admin import MoveGameAdminCommand
from .commands.missing_game_release_year_admin import MissingGRYAdminCommand
from .commands.missing_cover import MissingCoverAdminCommand
from .commands.set_platform_colors import SetPlatformColorsCommand
from .commands.get_platform import GetPlatformCommand
from .commands.set_platform_icon import SetPlatformIconCommand
from .commands.hide_game import HideGameCommand
from .commands.set_parent import SetParentCommand
from .commands.igdb_search import SearchIGDBCommand

REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchGamesCommand(),
    SearchSGDBCommand(),
    SearchIGDBCommand(),
    AddGameSGDBCommand(),
    AddGameIGDBCommand(),
    # manual
    StartManualCommand(),
    StopManualCommand(),
    AbortManualCommand(),
    TimeManualCommand(),
    # platform
    ListPlatformsCommand(),
    GetPlatformCommand(),
    SetDefaultPlatformCommand(),
    SetPCPlatformCommand(),
    # activity mgmt
    LastActivityCommand(),
    AddActivityCommand(),
    SetPlatformCommand(),
    SetGameCommand(),
    MoveGameCommand(),
    ToggleEmulatedCommand(),
    DeleteActivityCommand(),
    # gets
    GetActivityCommand(),
    GetGameCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
    AddGameAdminCommand(),
    # sgdb
    SetSGDBIDCommand(),
    SetSGDBGridIDCommand(),
    AutoSGDBAdminCommand(),
    MissingSGDBAdminCommand(),
    # steam
    SetSteamIDCommand(),
    # igdb
    SetIGDBIDCommand(),
    MissingIGDBAdminCommand(),
    AutoIGDBAdminCommand(),
    # manual game
    SetGameImageCommand(),
    SetGameReleaseYearCommand(),
    # platform mgmt
    AddPlatformCommand(),
    SetPlatformNameCommand(),
    SetPlatformColorsCommand(),
    SetPlatformIconCommand(),
    DeletePlatformCommand(),
    # game mgmt
    AddGameAliasCommand(),
    DeleteGameAliasCommand(),
    DeleteGameCommand(),
    GamesWithoutActivityAdminCommand(),
    HideGameCommand(),
    SetParentCommand(),
    # user mgmt
    SearchUsersCommand(),
    AddPermissionCommand(),
    RemovePermissionCommand(),
    SetGameAdminCommand(),
    MoveGameAdminCommand(),
    DeleteActivityAdminCommand(),
    # misc
    UptimeCommand(),
    MissingCoverAdminCommand(),
    MissingGRYAdminCommand(),
    GetCacheStats(),
    RefreshSearch(),
]

used = set()
for c in [*REGULAR_COMMANDS, *ADMIN_COMMANDS]:
    for name in c.names:
        if name in used:
            assert False, f"Duplicate command name: {name}"
        used.add(name)
