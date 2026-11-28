"""
Who is playing what right now, from manual tracking (LiveActivity) and Discord presence
(DiscordPresence). Only what would end up as an activity is shown, so the same checks as
when the session is stored: permissions, and Discord games mapped like the sync does
"""

import datetime
from typing import Literal

from tpbackend.activity.models import API_Playing
from tpbackend.discord.presence import STALE_AFTER
from tpbackend.game.select import GameSelect
from tpbackend.oblivionis import sync
from tpbackend.permissions import Permission
from tpbackend.storage import DiscordPresence, Game, LiveActivity, Platform, User
from tpbackend.utils2 import dt_to_ts


def playing_now(
    now: datetime.datetime, user_id: int | None = None
) -> list[API_Playing]:
    """
    newest first, each user, game and platform once. user_id: only that user, then
    private users are there too (it's their own page, check_user_filter is up to the
    caller)
    """
    playing: dict[tuple[int, int, int], API_Playing] = {}

    def add(
        user: User,
        game: Game,
        platform: Platform,
        started: datetime.datetime,
        source: Literal["manual", "discord"],
    ):
        if game.get_hidden() or user.has_permission(Permission.HIDE_PLAYING):
            return
        if user_id is not None and user.get_id() != user_id:
            return
        if user_id is None and user.has_permission(Permission.PRIVATE):
            return
        key = (user.get_id(), game.get_id(), platform.get_id())
        started_ts = dt_to_ts(started)
        # tracked both manually and by Discord: the earliest start
        if key in playing and playing[key].started <= started_ts:
            return
        playing[key] = API_Playing(
            user_id=user.get_id(),
            game_id=game.get_id(),
            platform_id=platform.get_id(),
            started=started_ts,
            source=source,
        )

    for live in LiveActivity.select():
        user = live.get_user()
        if user.has_permission(Permission.MANUAL_ACTIVITY):
            add(
                user,
                live.get_game(),
                live.get_platform(),
                live.get_started_datetime(),
                "manual",
            )

    presences = list(DiscordPresence.select())
    discord_ids = [p.get_discord_user_id() for p in presences]
    users = {
        u.get_discord_id(): u
        for u in User.select().where(User.discord_id << discord_ids)
    }
    for presence in presences:
        if now - presence.get_last_seen() > STALE_AFTER:
            # the bot isn't watching, they may have stopped
            continue
        user = users.get(presence.get_discord_user_id())
        # no user yet: created when the session is stored
        if not user or not user.has_permission(Permission.OBLIVIONIS_SYNC):
            continue
        # unknown games and platforms are created when the session is stored
        game = GameSelect.by_name_or_alias(sync.game_name(presence.get_game_name()))
        platform = Platform.get_or_none(
            Platform.abbreviation
            == sync.platform_abbreviation(user, presence.get_platform())
        )
        if not game or not platform:
            continue
        # like the duration when it's stored
        started = presence.get_started()
        discord_started = presence.get_discord_started()
        if discord_started and discord_started < started:
            started = discord_started
        add(user, game, platform, started, "discord")

    return sorted(playing.values(), key=lambda p: p.started, reverse=True)
