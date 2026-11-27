import discord

from tpbackend.admin.models import Admin_DiscordActivity


def test_discord_activity():
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name="Some Game",
        details="In menus",
        state="Solo",
        platform="ps5",
        timestamps={"start": 1795000000000},
    )
    assert Admin_DiscordActivity.from_activity(activity) == Admin_DiscordActivity(
        type="playing",
        name="Some Game",
        details="In menus",
        state="Solo",
        platform="ps5",
        start=1795000000000,
    )


def test_discord_activity_without_details():
    assert Admin_DiscordActivity.from_activity(
        discord.Game("Some Game")
    ) == Admin_DiscordActivity(
        type="playing",
        name="Some Game",
        details=None,
        state=None,
        platform=None,
        start=None,
    )
