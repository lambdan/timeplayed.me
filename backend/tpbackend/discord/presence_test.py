import datetime
from types import SimpleNamespace

import discord

from tpbackend.discord.presence import Playing, playing_from_activities

START = datetime.datetime(2026, 11, 22, 12, 0, tzinfo=datetime.UTC)


def activity(name: str, type=discord.ActivityType.playing, **kwargs):
    return SimpleNamespace(name=name, type=type, start=START, **kwargs)


def test_first_game_is_used():
    activities = [
        activity("Spotify", type=discord.ActivityType.listening),
        activity("Some Game", platform="ps5"),
        activity("Other Game"),
    ]
    assert playing_from_activities(activities) == Playing("Some Game", "ps5", START)


def test_nothing_playing():
    assert playing_from_activities([]) is None
    assert (
        playing_from_activities([activity("x", type=discord.ActivityType.listening)])
        is None
    )


def test_platform_defaults_to_pc():
    assert playing_from_activities([activity("A")]).platform == "pc"
    assert playing_from_activities([activity("A", platform=None)]).platform == "pc"
    assert playing_from_activities([activity("A", platform="desktop")]).platform == "pc"


def test_steam_deck_puts_the_game_in_details():
    playing = playing_from_activities([activity("Steam Deck", details="Playing Hades")])
    assert playing == Playing("Hades", "steamdeck", START)


def test_no_start():
    playing = playing_from_activities(
        [SimpleNamespace(name="A", type=discord.ActivityType.playing)]
    )
    assert playing == Playing("A", "pc", None)
