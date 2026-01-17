from tpbackend.cmds.add_game import AddGameCommand
from tpbackend.cmds.search import SearchCommand
from tpbackend.cmds.set_game import SetGameCommand


REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchCommand(),
    AddGameCommand(),
    SetGameCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
]
