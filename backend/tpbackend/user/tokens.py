from typing import cast
from tpbackend.storage import Token, User
import hashlib
import secrets


def generate_token(user: User) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    Token.create(
        user=user,
        sha256=token_hash,
    )
    return token


def lookup_token(token: str) -> Token | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    maybe = Token.get_or_none(sha256=token_hash)
    if maybe:
        maybe = cast(Token, maybe)
        if not maybe.is_expired():
            return maybe
    return None
