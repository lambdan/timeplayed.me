import discord
from fastapi import APIRouter

from tpbackend.admin.models import (
    Admin_DiscordActivity,
    Admin_Presence,
    Admin_PresenceMember,
    Admin_TrackedPresence,
)
from tpbackend.discord import presence
from tpbackend.discord.bot import bot
from tpbackend.permissions import Permission
from tpbackend.storage import DiscordPresence, User
from tpbackend.utils2 import dt_to_ts_or_none

router = APIRouter()


@router.get("/presence", response_model=Admin_Presence)
def get_presence() -> Admin_Presence:
    """
    What the presence tracker sees right now: the sessions it tracks, and the Discord
    activities of everyone playing something
    """
    tracked = {p.get_discord_user_id(): p for p in DiscordPresence.select()}
    names = {
        discord_user_id: p.get_discord_user_name()
        for discord_user_id, p in tracked.items()
    }
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
        tracked_presence = None
        if discord_user_id in tracked:
            tracked_presence = Admin_TrackedPresence.from_presence(
                tracked[discord_user_id]
            )
        members.append(
            Admin_PresenceMember(
                discord_user_id=discord_user_id,
                discord_user_name=name,
                user_id=user.get_id() if user else None,
                # new users get it by default
                synced=not user or user.has_permission(Permission.OBLIVIONIS_SYNC),
                tracked=tracked_presence,
                activities=activities.get(discord_user_id, []),
            )
        )
    members.sort(key=lambda m: m.discord_user_name.casefold())

    return Admin_Presence(
        connected=bot.is_ready() and not bot.is_closed(),
        last_checked=dt_to_ts_or_none(presence.last_checked),
        members=members,
    )
