"""
Tracks what Discord users play from their presence, like Oblivionis does, but persistent:
the session is stored when they start playing and checked every minute, so a session
survives the bot restarting. Every game they play at the same time is tracked (Oblivionis
only tracks the first). Sessions go through the same path as the Oblivionis sync, so when
both see the same session, the overlap check merges them
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
from tpbackend.storage import DiscordHistory, DiscordPresence

logger = logging.getLogger("discord-presence")

SOURCE = "Discord presence"
# DiscordHistory event for what the tracker does, and for what Discord says they're doing
HISTORY_EVENT = "presence"
ACTIVITIES_HISTORY_EVENT = "activities"
CHECK_INTERVAL_SECONDS = 60
# when a session hasn't been seen for this long, the bot wasn't watching (it was down),
# so they may have stopped any time since it was last seen
STALE_AFTER = datetime.timedelta(minutes=5)

# when check_loop last checked everyone without failing, shown on the admin page
last_checked: datetime.datetime | None = None


@dataclass
class Playing:
    game_name: str
    platform: str
    # when Discord says they started, None if it didn't say
    started: datetime.datetime | None


def playing_from_activities(activities) -> list[Playing]:
    """
    The games in a member's activities, mapped like Oblivionis does. They can play several
    at the same time, each game and platform is in it once
    """
    playing = []
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
        if any(p.game_name == game_name and p.platform == platform for p in playing):
            continue
        playing.append(Playing(game_name, platform, getattr(activity, "start", None)))
    return playing


# what else an activity says, for the Discord history. title and artist are Spotify's
DESCRIBED_FIELDS = ["details", "state", "title", "artist"]


def describe_activities(activities) -> str:
    """
    What a member is doing according to Discord, for their Discord history
    """
    parts = []
    for activity in activities:
        part = f"{activity.type.name} '{activity.name}'"
        platform = getattr(activity, "platform", None)
        if platform:
            part += f" ({platform})"
        fields = []
        for field in DESCRIBED_FIELDS:
            value = getattr(activity, field, None)
            if value:
                fields.append(f"{field}: '{value}'")
        if fields:
            part += f" [{', '.join(fields)}]"
        parts.append(part)
    return ", ".join(parts) or "nothing"


def add_history(discord_user_id: str, message: str, now: datetime.datetime):
    DiscordHistory.create(
        timestamp=now, event=HISTORY_EVENT, user=discord_user_id, message=message
    )


def is_same_game(presence: DiscordPresence, playing: Playing) -> bool:
    return (
        presence.get_game_name() == playing.game_name
        and presence.get_platform() == playing.platform
    )


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
        add_history(
            presence.get_discord_user_id(),
            f"Stopped playing '{presence.get_game_name()}' ({presence.get_platform()}) right away, not stored ({reason})",
            ended,
        )
        return
    details = f", first seen: {js_iso(presence.get_started())}"
    if discord_started:
        details += f", Discord start: {js_iso(discord_started)}"
    details += f", ended: {js_iso(ended)} ({reason})"
    _, outcome = sync.parseActivity(
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
    add_history(
        presence.get_discord_user_id(),
        f"Stopped playing '{presence.get_game_name()}' ({presence.get_platform()}) after {seconds} seconds ({reason}): {outcome}",
        ended,
    )


def update(
    discord_user_id: str,
    discord_user_name: str,
    playing: list[Playing],
    now: datetime.datetime,
):
    """
    What the user is playing right now (empty if nothing). Starts, keeps or ends a session
    for each game
    """
    sessions = []
    for presence in DiscordPresence.select().where(
        DiscordPresence.discord_user_id == discord_user_id
    ):
        if now - presence.get_last_seen() > STALE_AFTER:
            close(presence, presence.get_last_seen(), "not seen since, bot was down")
        else:
            sessions.append(presence)

    new_games = [
        game
        for game in playing
        if not any(is_same_game(presence, game) for presence in sessions)
    ]

    for presence in sessions:
        game = next((g for g in playing if is_same_game(presence, g)), None)
        if game is None:
            reason = "started something else" if new_games else "stopped playing"
            close(presence, now, reason)
            continue
        # still playing: keep our start, and Discord's earliest. Some games reset
        # Discord's start mid-session, and Discord doesn't always say
        discord_started = presence.get_discord_started()
        if game.started and (discord_started is None or game.started < discord_started):
            presence.discord_started = game.started
        presence.last_seen = now
        presence.save()

    for game in new_games:
        logger.info(
            "%s started playing %s (%s)",
            discord_user_name,
            game.game_name,
            game.platform,
        )
        message = f"Started playing '{game.game_name}' ({game.platform})"
        if game.started:
            message += f", Discord start: {js_iso(game.started)}"
        add_history(discord_user_id, message, now)
        DiscordPresence.create(
            discord_user_id=discord_user_id,
            discord_user_name=discord_user_name,
            game_name=game.game_name,
            platform=game.platform,
            started=now,
            discord_started=game.started,
            last_seen=now,
        )


def members():
    """
    Every member the bot sees (not bots), once even if they're in several servers
    """
    seen = set()
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot or member.id in seen:
                continue
            seen.add(member.id)
            yield member


def check_all(now: datetime.datetime):
    tracked = {
        p.get_discord_user_id(): p.get_discord_user_name()
        for p in DiscordPresence.select()
    }
    checked = set()
    for member in members():
        discord_user_id = str(member.id)
        checked.add(discord_user_id)
        playing = playing_from_activities(member.activities)
        if playing or discord_user_id in tracked:
            update(discord_user_id, member.name, playing, now)
    # not in any server anymore, so not playing
    for discord_user_id, discord_user_name in tracked.items():
        if discord_user_id not in checked:
            update(discord_user_id, discord_user_name, [], now)


async def check_loop():
    global last_checked
    await bot.wait_until_ready()
    while True:
        try:
            now = utils2.now()
            check_all(now)
            last_checked = now
        except Exception as e:
            logger.error("Checking presences failed: %s", e)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.bot:
        return
    try:
        # what Discord says, before the tracker maps it, to see what it didn't pick up
        described = describe_activities(after.activities)
        if described != describe_activities(before.activities):
            DiscordHistory.create(
                event=ACTIVITIES_HISTORY_EVENT, user=str(after.id), message=described
            )
    except Exception as e:
        logger.error("Storing activities of %s failed: %s", after.name, e)
    try:
        update(
            str(after.id),
            after.name,
            playing_from_activities(after.activities),
            utils2.now(),
        )
    except Exception as e:
        logger.error("Updating presence of %s failed: %s", after.name, e)
