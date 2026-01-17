from tpbackend.cmds.add_game import AddGameCommand
from tpbackend.cmds.search import SearchCommand


REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchCommand(),
    AddGameCommand(),
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
]
