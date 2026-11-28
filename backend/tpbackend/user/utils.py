from tpbackend.api.responses import not_found
from tpbackend.globals import timeplayed_url
from tpbackend.storage import User


def user_url(user_id) -> str:
    return f"{timeplayed_url()}/user/{user_id}"


def check_user_filter(user_ids: list[int] | int | str | None, viewer: User | None):
    """
    Filtering by a private user is a 404 like they don't exist, but to themselves (their
    own user page)
    """
    if user_ids is None:
        return
    if not isinstance(user_ids, list):
        user_ids = [int(user_ids)]
    for user in User.select().where(User.id.in_(user_ids)):  # type: ignore
        if user.is_private_to(viewer):
            not_found("User not found")
