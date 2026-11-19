from .commands.token_generate import TokenGenerateCommand
from .commands.token_revoke_all import TokenRevokeAllCommand

# everything else is on the website, the bot is for tracking and getting a token
COMMANDS = [
    TokenGenerateCommand(),
    TokenRevokeAllCommand(),
]

used = set()
for c in COMMANDS:
    for name in c.names:
        if name in used:
            assert False, f"Duplicate command name: {name}"
        used.add(name)
