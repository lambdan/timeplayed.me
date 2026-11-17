from tpbackend.globals import timeplayed_url
from tpbackend.storage import Activity


def activity_url(activity_id) -> str:
    return f"{timeplayed_url()}/activity/{activity_id}"


def md_activity_link(game: int | Activity) -> str:
    if isinstance(game, int):
        game = Activity.get_by_id(game)
    assert isinstance(game, Activity)
    id = game.get_id()
    name = f"Activity {id}".strip()
    url = activity_url(id)
    return f"[{name}]({url})"
