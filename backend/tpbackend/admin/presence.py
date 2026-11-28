from collections import defaultdict

import discord
from fastapi import APIRouter

from tpbackend.admin.models import (
    Admin_DiscordActivity,
    Admin_LiveActivity,
    Admin_Presence,
    Admin_PresenceMember,
    Admin_TrackedPresence,
)
from tpbackend.discord import presence
from tpbackend.discord.bot import bot
from tpbackend.permissions import Permission
from tpbackend.storage import DiscordPresence, LiveActivity, User
from tpbackend.api.responses import not_found
from tpbackend.utils2 import dt_to_ts_or_none, js_iso

router = APIRouter()


@router.get("/presence", response_model=Admin_Presence)
def get_presence() -> Admin_Presence:
    """
    What the presence tracker sees right now: the sessions it tracks, and the Discord
    activities of everyone playing something
    """
    tracked = defaultdict(list)
    names = {}
    for p in DiscordPresence.select().order_by(DiscordPresence.started):
        tracked[p.get_discord_user_id()].append(Admin_TrackedPresence.from_presence(p))
        names[p.get_discord_user_id()] = p.get_discord_user_name()
    activities = {}
    # read from the bot's cache in the thread pool, which is fine for a snapshot:
    # discord.py replaces a member's activities instead of changing them
    for member in presence.members():
        discord_user_id = str(member.id)
        playing = presence.playing_from_activities(member.activities)
        if not playing and discord_user_id not in tracked:
            continue
        names[discord_user_id] = member.name
        # custom status is text the user wrote, not something they do
        activities[discord_user_id] = [
            Admin_DiscordActivity.from_activity(a)
            for a in member.activities
            if a.type != discord.ActivityType.custom
        ]

    users = {
        u.get_discord_id(): u
        for u in User.select().where(User.discord_id << list(names))
    }
    members = []
    for discord_user_id, name in names.items():
        user = users.get(discord_user_id)
        members.append(
            Admin_PresenceMember(
                discord_user_id=discord_user_id,
                discord_user_name=name,
                user_id=user.get_id() if user else None,
                # new users get it by default
                synced=not user or user.has_permission(Permission.DISCORD_TRACKING),
                tracked=tracked.get(discord_user_id, []),
                activities=activities.get(discord_user_id, []),
            )
        )
    members.sort(key=lambda m: m.discord_user_name.casefold())

    return Admin_Presence(
        connected=bot.is_ready() and not bot.is_closed(),
        last_checked=dt_to_ts_or_none(presence.last_checked),
        members=members,
    )


@router.get("/live", response_model=list[Admin_LiveActivity])
def get_live_activities() -> list[Admin_LiveActivity]:
    """running manual tracking sessions, newest first"""
    return [
        Admin_LiveActivity.from_live_activity(live)
        for live in LiveActivity.select().order_by(LiveActivity.started.desc())
    ]


@router.delete("/live/{live_activity_id}")
def discard_live_activity(live_activity_id: int):
    """
    For a session someone forgot to stop: it's removed and nothing is stored, since
    stopping it would store all the time it was left running
    """
    live = LiveActivity.get_or_none(LiveActivity.id == live_activity_id)
    if not live:
        return not_found("Live activity not found")
    user = live.get_user()
    user.add_history(
        f"Manual tracking discarded by admin (game: '{live.get_game().get_name()}', platform: '{live.get_platform().get_abbreviation()}', started: {js_iso(live.get_started_datetime())})"
    )
    user.save()
    live.delete_instance()
    return "Discarded"
