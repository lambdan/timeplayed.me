from typing import cast
from tpbackend.storage import Activity_or_none, Token, User
import uuid
import hashlib
import base64

def generate_token(user: User) -> Token:
    uuid_str = str(uuid.uuid4())
    sha256_str = hashlib.sha256(uuid_str.encode()).hexdigest()
    token = Token.create(user=user, sha256=sha256_str)
    return cast(Token, token)


def to_base64_str(token: Token) -> str:
    return base64.b64encode(token.get_sha256().encode("utf-8")).decode("utf-8")


def from_base64_str(encoded: str) -> Token | None:
    try:
        decoded_bytes = base64.b64decode(encoded)
        decoded_str = decoded_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError("Invalid base64 string") from e

    token = Token.select().where(Token.sha256 == decoded_str).first()
    return cast(Token | None, token)
