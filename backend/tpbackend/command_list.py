from tpbackend.cmds.add_activity import AddActivityCommand
from tpbackend.cmds.add_game import AddGameCommand
from tpbackend.cmds.delete_activity import DeleteActivityCommand
from tpbackend.cmds.emulated import ToggleEmulatedCommand
from tpbackend.cmds.last import LastActivityCommand
from tpbackend.cmds.search import SearchCommand
from tpbackend.cmds.set_game import SetGameCommand
from tpbackend.cmds.set_platform import SetPlatformCommand
from tpbackend.cmds.start_manual import StartManualCommand
from tpbackend.cmds.stop_manual import StopManualCommand


REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchCommand(),
    AddGameCommand(),
    SetGameCommand(),
    SetPlatformCommand(),
    AddActivityCommand(),
    ToggleEmulatedCommand(),
    DeleteActivityCommand(),
    LastActivityCommand(),
    StartManualCommand(),
    StopManualCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
]
