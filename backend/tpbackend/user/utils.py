from tpbackend.globals import timeplayed_url


def user_url(user_id) -> str:
    return f"{timeplayed_url()}/user/{user_id}"
