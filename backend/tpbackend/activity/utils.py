from tpbackend.globals import timeplayed_url


def activity_url(activity_id) -> str:
    return f"{timeplayed_url()}/activity/{activity_id}"
