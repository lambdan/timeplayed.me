import datetime
from types import SimpleNamespace

import discord

from tpbackend.discord import presence
from tpbackend.discord.presence import Playing, playing_from_activities

START = datetime.datetime(2026, 11, 22, 12, 0, tzinfo=datetime.UTC)


def activity(name: str, type=discord.ActivityType.playing, **kwargs):
    return SimpleNamespace(name=name, type=type, start=START, **kwargs)


def test_every_game_is_used():
    activities = [
        activity("Spotify", type=discord.ActivityType.listening),
        activity("Some Game", platform="ps5"),
        activity("Other Game"),
    ]
    assert playing_from_activities(activities) == [
        Playing("Some Game", "ps5", START),
        Playing("Other Game", "pc", START),
    ]


def test_same_game_twice_is_once():
    activities = [activity("Game"), activity("Game", platform="desktop")]
    assert playing_from_activities(activities) == [Playing("Game", "pc", START)]


def test_same_game_on_two_platforms_is_both():
    activities = [activity("Game"), activity("Game", platform="ps5")]
    assert len(playing_from_activities(activities)) == 2


def test_nothing_playing():
    assert playing_from_activities([]) == []
    assert (
        playing_from_activities([activity("x", type=discord.ActivityType.listening)])
        == []
    )


def test_platform_defaults_to_pc():
    for platform in (None, "desktop"):
        [playing] = playing_from_activities([activity("A", platform=platform)])
        assert playing.platform == "pc"
    [playing] = playing_from_activities([activity("A")])
    assert playing.platform == "pc"


def test_steam_deck_puts_the_game_in_details():
    playing = playing_from_activities([activity("Steam Deck", details="Playing Hades")])
    assert playing == [Playing("Hades", "steamdeck", START)]


def test_no_start():
    playing = playing_from_activities(
        [SimpleNamespace(name="A", type=discord.ActivityType.playing)]
    )
    assert playing == [Playing("A", "pc", None)]


def test_members_skips_bots_and_duplicates(monkeypatch):
    alice = SimpleNamespace(id=1, bot=False)
    bot_member = SimpleNamespace(id=2, bot=True)
    bob = SimpleNamespace(id=3, bot=False)
    guilds = [
        SimpleNamespace(members=[alice, bot_member]),
        # alice is in both servers
        SimpleNamespace(members=[bob, alice]),
    ]
    monkeypatch.setattr(presence, "bot", SimpleNamespace(guilds=guilds))
    assert list(presence.members()) == [alice, bob]


def test_describe_activities():
    activities = [
        activity("World of Warcraft: Forever"),
        activity("Some Game", platform="ps5"),
        activity(
            "Spotify",
            type=discord.ActivityType.listening,
            title="Song",
            artist="Band",
        ),
        activity("Rich Game", details="In a dungeon", state="Party of 3"),
    ]
    assert presence.describe_activities(activities) == (
        "playing 'World of Warcraft: Forever', playing 'Some Game' (ps5), "
        "listening 'Spotify' [title: 'Song', artist: 'Band'], "
        "playing 'Rich Game' [details: 'In a dungeon', state: 'Party of 3']"
    )
    assert presence.describe_activities([]) == "nothing"
