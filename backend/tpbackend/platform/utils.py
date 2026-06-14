from tpbackend.globals import TIMEPLAYED_URL
from tpbackend.storage import Platform, Game, User, Activity
from tpbackend.activity.query import ActivityQuery
from typing import cast


def display_name(platform: int | Platform) -> str:
    if isinstance(platform, int):
        platform = Platform.get_by_id(platform)
    assert isinstance(platform, Platform)
    return (platform.get_name() or platform.get_abbreviation()).strip()


def platform_url(platform_id) -> str:
    return f"{TIMEPLAYED_URL}/platform/{platform_id}"


def md_platform_link(platform: int | Platform) -> str:
    if isinstance(platform, int):
        platform = Platform.get_by_id(platform)
    assert isinstance(platform, Platform)
    id = platform.get_id()
    name = display_name(platform)
    url = platform_url(id)
    return f"[{name}]({url})"


def last_platform_for_game(user: User, game: Game) -> Platform | None:
    """
    Returns the last platform the user played the game on if available
    """
    a = ActivityQuery.base()
    a = ActivityQuery.user(a, user)
    a = ActivityQuery.game(a, game)
    a = ActivityQuery.apply_sort(a, "timestamp", "desc")
    a = a.first()
    if a:
        a = cast(Activity, a)
        return a.get_platform()
    return None
