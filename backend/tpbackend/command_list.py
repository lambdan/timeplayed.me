from tpbackend.cmds.add_activity import AddActivityCommand
from tpbackend.cmds.add_game_sgdb import AddGameSGDBCommand
from tpbackend.cmds.add_game_admin import AddGameAdminCommand
from tpbackend.cmds.add_platform import AddPlatformCommand
from tpbackend.cmds.block_commands import BlockCommandsCommand
from tpbackend.cmds.delete_activity import DeleteActivityCommand
from tpbackend.cmds.delete_game import DeleteGameCommand
from tpbackend.cmds.delete_platform import DeletePlatformCommand
from tpbackend.cmds.emulated import ToggleEmulatedCommand
from tpbackend.cmds.get_activity import GetActivityCommand
from tpbackend.cmds.get_game import GetGameCommand
from tpbackend.cmds.last import LastActivityCommand
from tpbackend.cmds.search_games import SearchGamesCommand
from tpbackend.cmds.set_default_platform import SetDefaultPlatformCommand
from tpbackend.cmds.set_game import SetGameCommand
from tpbackend.cmds.set_game_image import SetGameImageCommand
from tpbackend.cmds.set_pc_platform import SetPCPlatformCommand
from tpbackend.cmds.set_platform import SetPlatformCommand
from tpbackend.cmds.set_platform_name import SetPlatformNameCommand
from tpbackend.cmds.set_sgdb_id import SetSGDBIDCommand
from tpbackend.cmds.start_manual import StartManualCommand
from tpbackend.cmds.stop_manual import StopManualCommand
from tpbackend.cmds.list_platforms import ListPlatformsCommand
from tpbackend.cmds.set_steam_id import SetSteamIDCommand
from tpbackend.cmds.add_game_alias import AddGameAliasCommand
from tpbackend.cmds.delete_game_alias import DeleteGameAliasCommand
from tpbackend.cmds.set_game_release_year import SetGameReleaseYearCommand
from tpbackend.cmds.search_users import SearchUsersCommand
from tpbackend.cmds.uptime import UptimeCommand
from tpbackend.cmds.set_game_admin import SetGameAdminCommand
from tpbackend.cmds.delete_activity_admin import DeleteActivityAdminCommand
from tpbackend.cmds.abort_manual import AbortManualCommand
from tpbackend.cmds.time_manual import TimeManualCommand
from tpbackend.cmds.missing_sgdb_admin import MissingSGDBAdminCommand
from tpbackend.cmds.search_sgdb import SearchSGDBCommand

REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchGamesCommand(),
    SearchSGDBCommand(),
    AddGameSGDBCommand(),
    # manual
    StartManualCommand(),
    StopManualCommand(),
    AbortManualCommand(),
    TimeManualCommand(),
    # platform
    ListPlatformsCommand(),
    SetDefaultPlatformCommand(),
    SetPCPlatformCommand(),
    # activity mgmt
    LastActivityCommand(),
    AddActivityCommand(),
    SetPlatformCommand(),
    SetGameCommand(),
    ToggleEmulatedCommand(),
    DeleteActivityCommand(),
    # gets
    GetActivityCommand(),
    GetGameCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
    AddGameAdminCommand(),
    SetSGDBIDCommand(),
    SetSteamIDCommand(),
    SetGameImageCommand(),
    SetGameReleaseYearCommand(),
    # platform mgmt
    AddPlatformCommand(),
    SetPlatformNameCommand(),
    DeletePlatformCommand(),
    # gmae mgmt
    AddGameAliasCommand(),
    DeleteGameAliasCommand(),
    DeleteGameCommand(),
    # user mgmt
    BlockCommandsCommand(),
    SearchUsersCommand(),
    SetGameAdminCommand(),
    DeleteActivityAdminCommand(),
    # misc
    UptimeCommand(),
    MissingSGDBAdminCommand(),
]

used = set()
for c in [*REGULAR_COMMANDS, *ADMIN_COMMANDS]:
    for name in c.names:
        if name in used:
            assert False, f"Duplicate command name: {name}"
        used.add(name)
