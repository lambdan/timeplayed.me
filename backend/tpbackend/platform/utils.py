from tpbackend.globals import timeplayed_url
from tpbackend.storage import Platform


def display_name(platform: int | Platform) -> str:
    if isinstance(platform, int):
        platform = Platform.get_by_id(platform)
    assert isinstance(platform, Platform)
    return (platform.get_name() or platform.get_abbreviation()).strip()


def platform_url(platform_id) -> str:
    return f"{timeplayed_url()}/platform/{platform_id}"


def md_platform_link(platform: int | Platform) -> str:
    if isinstance(platform, int):
        platform = Platform.get_by_id(platform)
    assert isinstance(platform, Platform)
    id = platform.get_id()
    name = display_name(platform)
    url = platform_url(id)
    return f"[{name}]({url})"
