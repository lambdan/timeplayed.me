from typing import cast
from tpbackend.storage import Activity_or_none, Token, User
from .command import Command


class TokenGenerateCommand(Command):
    def __init__(self):
        names = ["token"]
        d = "Generates a token for your user"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        token = Token.create(user=user)
        token = cast(Token, token)
        return f"Token generated: ```{token.get_id()}```It will expire at {token.get_expires()}"
