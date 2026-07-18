from tpbackend.storage import User
from tpbackend.user.tokens import generate_token
from .command import Command
import base64


class TokenGenerateCommand(Command):
    def __init__(self):
        names = ["token"]
        d = "Generates a token for your user"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        new_token = generate_token(user)
        return f"Generated new token for you: ```{new_token}```"
