"""
Tracks what Discord users play from their presence, like Oblivionis does, but persistent:
the session is stored when they start playing and checked every minute, so a session
survives the bot restarting. Sessions go through the same path as the Oblivionis sync,
so when both see the same session, the overlap check merges them
"""

import asyncio
import datetime
import logging
from dataclasses import dataclass

import discord

from tpbackend import utils2
from tpbackend.utils2 import js_iso
from tpbackend.discord.bot import bot
from tpbackend.oblivionis import sync
from tpbackend.storage import DiscordPresence

logger = logging.getLogger("discord-presence")

SOURCE = "Discord presence"
CHECK_INTERVAL_SECONDS = 60
# when a session hasn't been seen for this long, the bot wasn't watching (it was down),
# so they may have stopped any time since it was last seen
STALE_AFTER = datetime.timedelta(minutes=5)


@dataclass
class Playing:
    game_name: str
    platform: str
    # when Discord says they started, None if it didn't say
    started: datetime.datetime | None


def playing_from_activities(activities) -> Playing | None:
    """
    The game in a member's activities, mapped like Oblivionis does
    """
    for activity in activities:
        if activity.type != discord.ActivityType.playing:
            continue
        game_name = activity.name
        platform = getattr(activity, "platform", None) or "pc"
        if activity.name == "Steam Deck":
            # Decky Discord Status plugin will sometimes say game name is "Steam Deck",
            # and put actual game name in details
            game_name = (activity.details or "").removeprefix("Playing ")
            platform = "steamdeck"
        if platform == "desktop":
            # Some games say "desktop", lets just lump it together with "pc"
            platform = "pc"
        return Playing(game_name, platform, getattr(activity, "start", None))
    return None


def close(presence: DiscordPresence, ended: datetime.datetime, reason: str):
    # some games reset Discord's start mid-session, and Discord's start is from before the
    # bot saw them if the bot started later, so the longer of the two wins
    # rounded like Oblivionis does, so the same session gets the same duration
    seconds = round((ended - presence.get_started()).total_seconds())
    discord_started = presence.get_discord_started()
    if discord_started:
        seconds = max(seconds, round((ended - discord_started).total_seconds()))
    logger.info(
        "%s stopped playing %s (%s) after %s seconds",
        presence.get_discord_user_name(),
        presence.get_game_name(),
        presence.get_platform(),
        seconds,
    )
    presence.delete_instance()
    if seconds <= 0:
        # never seen playing after it started
        return
    details = f", first seen: {js_iso(presence.get_started())}"
    if discord_started:
        details += f", Discord start: {js_iso(discord_started)}"
    details += f", ended: {js_iso(ended)} ({reason})"
    sync.parseActivity(
        {
            "game_name": presence.get_game_name(),
            "duration": seconds,
            "dt": ended,
            "discord_user_name": presence.get_discord_user_name(),
            "discord_user_id": presence.get_discord_user_id(),
            "platform": presence.get_platform(),
        },
        source=SOURCE,
        ended=ended,
        details=details,
    )


def update(
    discord_user_id: str,
    discord_user_name: str,
    playing: Playing | None,
    now: datetime.datetime,
):
    """
    What the user is playing right now (None if nothing). Starts, keeps or ends their session
    """
    presence = DiscordPresence.get_or_none(
        DiscordPresence.discord_user_id == discord_user_id
    )

    if presence and now - presence.get_last_seen() > STALE_AFTER:
        close(presence, presence.get_last_seen(), "not seen since, bot was down")
        presence = None

    if (
        presence
        and playing
        and presence.get_game_name() == playing.game_name
        and presence.get_platform() == playing.platform
    ):
        # same game again: keep our start, and Discord's earliest. Some games reset
        # Discord's start mid-session, and Discord doesn't always say
        discord_started = presence.get_discord_started()
        if playing.started and (
            discord_started is None or playing.started < discord_started
        ):
            presence.discord_started = playing.started
        presence.last_seen = now
        presence.save()
        return

    if presence:
        reason = "started something else" if playing else "stopped playing"
        close(presence, now, reason)

    if playing:
        logger.info(
            "%s started playing %s (%s)",
            discord_user_name,
            playing.game_name,
            playing.platform,
        )
        DiscordPresence.create(
            discord_user_id=discord_user_id,
            discord_user_name=discord_user_name,
            game_name=playing.game_name,
            platform=playing.platform,
            started=now,
            discord_started=playing.started,
            last_seen=now,
        )


def check_all(now: datetime.datetime):
    tracked = {
        p.get_discord_user_id(): p.get_discord_user_name()
        for p in DiscordPresence.select()
    }
    checked = set()
    for guild in bot.guilds:
        for member in guild.members:
            discord_user_id = str(member.id)
            if member.bot or discord_user_id in checked:
                continue
            checked.add(discord_user_id)
            playing = playing_from_activities(member.activities)
            if playing or discord_user_id in tracked:
                update(discord_user_id, member.name, playing, now)
    # not in any server anymore, so not playing
    for discord_user_id, discord_user_name in tracked.items():
        if discord_user_id not in checked:
            update(discord_user_id, discord_user_name, None, now)


async def check_loop():
    await bot.wait_until_ready()
    while True:
        try:
            check_all(utils2.now())
        except Exception as e:
            logger.error("Checking presences failed: %s", e)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.bot:
        return
    try:
        update(
            str(after.id),
            after.name,
            playing_from_activities(after.activities),
            utils2.now(),
        )
    except Exception as e:
        logger.error("Updating presence of %s failed: %s", after.name, e)
