from tpbackend.cmds.add_activity import AddActivityCommand
from tpbackend.cmds.add_game import AddGameCommand
from tpbackend.cmds.delete_activity import DeleteActivityCommand
from tpbackend.cmds.emulated import ToggleEmulatedCommand
from tpbackend.cmds.last import LastActivityCommand
from tpbackend.cmds.search import SearchCommand
from tpbackend.cmds.set_default_platform import SetDefaultPlatformCommand
from tpbackend.cmds.set_game import SetGameCommand
from tpbackend.cmds.set_game_image import SetGameImageCommand
from tpbackend.cmds.set_pc_platform import SetPCPlatformCommand
from tpbackend.cmds.set_platform import SetPlatformCommand
from tpbackend.cmds.set_sgdb_id import SetSGDBIDCommand
from tpbackend.cmds.start_manual import StartManualCommand
from tpbackend.cmds.stop_manual import StopManualCommand
from tpbackend.cmds.list_platforms import ListPlatformsCommand
from tpbackend.cmds.set_steam_id import SetSteamIDCommand


REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchCommand(),
    ListPlatformsCommand(),
    AddGameCommand(),
    SetGameCommand(),
    SetPlatformCommand(),
    AddActivityCommand(),
    ToggleEmulatedCommand(),
    DeleteActivityCommand(),
    LastActivityCommand(),
    StartManualCommand(),
    StopManualCommand(),
    SetDefaultPlatformCommand(),
    SetPCPlatformCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
    SetSGDBIDCommand(),
    SetSteamIDCommand(),
    SetGameImageCommand(),
]
