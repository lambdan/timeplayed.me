from tpbackend.storage import Token, User
from .command import Command


class TokenRevokeAllCommand(Command):
    def __init__(self):
        names = ["revoke_tokens"]
        d = "Revokes all tokens for your user"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        tokens = Token.select().where(Token.user == user)
        count = 0
        for token in tokens:
            token.delete_instance()
            count += 1
        user.add_history(f"Revoked {count} tokens")
        user.save()
        return f"OK! Revoked {count} tokens."
