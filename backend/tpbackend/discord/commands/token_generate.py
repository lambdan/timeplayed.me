from tpbackend.globals import timeplayed_url
from tpbackend.storage import User
from tpbackend.user.tokens import generate_token
from .command import Command


class TokenGenerateCommand(Command):
    sensitive_reply = True

    def __init__(self):
        names = ["token"]
        d = f"Generate a token to log in on {timeplayed_url()}/login"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        new_token = generate_token(user)
        new_token_sub = new_token[:4] + "..." + new_token[-4:]
        user.add_history(f"Generated new token: {new_token_sub}")
        user.save()
        return (
            f"Generated new token for you: ```{new_token}```"
            f"Log in with it on {timeplayed_url()}/login"
        )
