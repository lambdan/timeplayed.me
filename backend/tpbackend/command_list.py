from tpbackend.cmds.search import SearchCommand


REGULAR_COMMANDS = [
    # HelpCommand(), # circular import
    SearchCommand()
]

ADMIN_COMMANDS = [
    # HelpAdminCommand(), # circular import
]
