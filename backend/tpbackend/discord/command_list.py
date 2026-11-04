from tpbackend.discord.commands.token_generate import TokenGenerateCommand
from tpbackend.discord.commands.token_revoke_all import TokenRevokeAllCommand
from .commands.add_activity import AddActivityCommand
from .commands.add_game_sgdb import AddGameSGDBCommand
from .commands.add_game_admin import AddGameAdminCommand
from .commands.add_platform_admin import AddPlatformAdminCommand
from .commands.delete_activity import DeleteActivityCommand
from .commands.delete_game_admin import DeleteGameAdminCommand
from .commands.delete_platform_admin import DeletePlatformAdminCommand
from .commands.get_activity import GetActivityCommand
from .commands.get_game import GetGameCommand
from .commands.last import LastActivityCommand
from .commands.permission_add_admin import AddPermissionAdminCommand
from .commands.permission_remove_admin import RemovePermissionAdminCommand
from .commands.refresh_search_admin import RefreshSearchAdminCommand
from .commands.search_games import SearchGamesCommand
from .commands.set_default_platform import SetDefaultPlatformCommand
from .commands.set_game import SetGameCommand
from .commands.set_game_image_admin import SetGameImageAdminCommand
from .commands.igdb_missing_admin import MissingIGDBAdminCommand
from .commands.igdb_set_id_admin import SetIGDBIDAdminCommand
from .commands.igdb_add_game import AddGameIGDBCommand
from .commands.igdb_auto_admin import AutoIGDBAdminCommand
from .commands.set_pc_platform import SetPCPlatformCommand
from .commands.set_platform import SetPlatformCommand
from .commands.set_platform_name_admin import SetPlatformNameAdminCommand
from .commands.set_sgdb_id_admin import SetSGDBIDAdminCommand
from .commands.start_manual import StartManualCommand
from .commands.stop_manual import StopManualCommand
from .commands.list_platforms import ListPlatformsCommand
from .commands.add_game_alias_admin import AddGameAliasAdminCommand
from .commands.delete_game_alias_admin import DeleteGameAliasAdminCommand
from .commands.set_game_release_year_admin import SetGameReleaseYearAdminCommand
from .commands.search_users import SearchUsersCommand
from .commands.uptime_admin import UptimeAdminCommand
from .commands.set_game_admin import SetGameAdminCommand
from .commands.delete_activity_admin import DeleteActivityAdminCommand
from .commands.abort_manual import AbortManualCommand
from .commands.time_manual import TimeManualCommand
from .commands.missing_sgdb_admin import MissingSGDBAdminCommand
from .commands.search_sgdb import SearchSGDBCommand
from .commands.auto_sgdb_admin import AutoSGDBAdminCommand
from .commands.games_without_activity_admin import GamesWithoutActivityAdminCommand
from .commands.move_game import MoveGameCommand
from .commands.move_game_admin import MoveGameAdminCommand
from .commands.merge_game_admin import MergeGameAdminCommand
from .commands.merge_overlaps_admin import MergeOverlapsAdminCommand
from .commands.missing_game_release_year_admin import MissingGRYAdminCommand
from .commands.missing_cover_admin import MissingCoverAdminCommand
from .commands.set_platform_colors_admin import SetPlatformColorsAdminCommand
from .commands.get_platform import GetPlatformCommand
from .commands.set_platform_icon_admin import SetPlatformIconAdminCommand
from .commands.hide_game_admin import HideGameAdminCommand
from .commands.set_parent_admin import SetParentAdminCommand
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
    DeleteActivityCommand(),
    # gets
    GetActivityCommand(),
    GetGameCommand(),
    # token
    TokenGenerateCommand(),
    TokenRevokeAllCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
    AddGameAdminCommand(),
    # sgdb
    SetSGDBIDAdminCommand(),
    AutoSGDBAdminCommand(),
    MissingSGDBAdminCommand(),
    # igdb
    SetIGDBIDAdminCommand(),
    MissingIGDBAdminCommand(),
    AutoIGDBAdminCommand(),
    # manual game
    SetGameImageAdminCommand(),
    SetGameReleaseYearAdminCommand(),
    # platform mgmt
    AddPlatformAdminCommand(),
    SetPlatformNameAdminCommand(),
    SetPlatformColorsAdminCommand(),
    SetPlatformIconAdminCommand(),
    DeletePlatformAdminCommand(),
    # game mgmt
    AddGameAliasAdminCommand(),
    DeleteGameAliasAdminCommand(),
    DeleteGameAdminCommand(),
    GamesWithoutActivityAdminCommand(),
    HideGameAdminCommand(),
    SetParentAdminCommand(),
    # user mgmt
    SearchUsersCommand(),
    AddPermissionAdminCommand(),
    RemovePermissionAdminCommand(),
    SetGameAdminCommand(),
    MoveGameAdminCommand(),
    MergeGameAdminCommand(),
    MergeOverlapsAdminCommand(),
    DeleteActivityAdminCommand(),
    # misc
    UptimeAdminCommand(),
    MissingCoverAdminCommand(),
    MissingGRYAdminCommand(),
    RefreshSearchAdminCommand(),
]

used = set()
for c in [*REGULAR_COMMANDS, *ADMIN_COMMANDS]:
    for name in c.names:
        if name in used:
            assert False, f"Duplicate command name: {name}"
        used.add(name)
