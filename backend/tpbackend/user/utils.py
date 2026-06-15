from tpbackend.globals import TIMEPLAYED_URL
from tpbackend.storage import User


def user_url(user_id) -> str:
    return f"{TIMEPLAYED_URL}/user/{user_id}"


def md_user_link(user: int | User) -> str:
    if isinstance(user, int):
        user = User.get_by_id(user)
    assert isinstance(user, User)
    id = user.get_id()
    name = user.get_name().strip()
    url = user_url(id)
    return f"[{name}]({url})"
