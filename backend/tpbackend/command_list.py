from tpbackend.cmds.add_activity import AddActivityCommand
from tpbackend.cmds.add_game import AddGameCommand
from tpbackend.cmds.add_platform import AddPlatformCommand
from tpbackend.cmds.delete_activity import DeleteActivityCommand
from tpbackend.cmds.delete_game import DeleteGameCommand
from tpbackend.cmds.delete_platform import DeletePlatformCommand
from tpbackend.cmds.emulated import ToggleEmulatedCommand
from tpbackend.cmds.last import LastActivityCommand
from tpbackend.cmds.search import SearchCommand
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


REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchCommand(),
    ListPlatformsCommand(),
    AddGameCommand(),
    LastActivityCommand(),
    # manual
    StartManualCommand(),
    StopManualCommand(),
    # platform
    SetDefaultPlatformCommand(),
    SetPCPlatformCommand(),
    # activity mgmt
    AddActivityCommand(),
    SetPlatformCommand(),
    SetGameCommand(),
    ToggleEmulatedCommand(),
    DeleteActivityCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
    SetSGDBIDCommand(),
    SetSteamIDCommand(),
    SetGameImageCommand(),
    # platform mgmt
    AddPlatformCommand(),
    SetPlatformNameCommand(),
    DeletePlatformCommand(),
    # gmae mgmt
    AddGameAliasCommand(),
    DeleteGameAliasCommand(),
    DeleteGameCommand(),
]
