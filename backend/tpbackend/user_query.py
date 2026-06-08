import logging
from typing import cast, Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.storage.storage_v2 import User, Game, Activity, Platform

logger = logging.getLogger("user_query")


class UserQuery:
    TOTAL_SECONDS = fn.SUM(
        Case(None, [(Activity.hidden == False, Activity.seconds)], 0)
    ).alias("total_seconds")

    ACTIVITY_COUNT = fn.COUNT(Case(None, [(Activity.hidden == False, 1)], None)).alias(
        "activity_count"
    )

    LAST_ACTIVITY = fn.MAX(
        Case(None, [(Activity.hidden == False, Activity.timestamp)], None)
    ).alias("last_activity")

    GAME_COUNT = fn.COUNT(
        fn.DISTINCT(Case(None, [(Activity.hidden == False, Activity.game)], None))
    ).alias("game_count")

    PLATFORM_COUNT = fn.COUNT(
        fn.DISTINCT(Case(None, [(Activity.hidden == False, Activity.platform)], None))
    ).alias("platform_count")

    AGGREGATES = {
        "playtime": TOTAL_SECONDS,
        "activity_count": ACTIVITY_COUNT,
        "last_activity": LAST_ACTIVITY,
        "game_count": GAME_COUNT,
        "platform_count": PLATFORM_COUNT,
    }

    SORTS = {
        **AGGREGATES,
        "name": User.name,
        "id": User.id,
    }

    SORTS_LITERAL = Literal[
        "playtime",
        "activity_count",
        "last_activity",
        "game_count",
        "platform_count",
        "name",
        "id",
    ]

    @staticmethod
    def base():
        return (
            User.select(User, *UserQuery.AGGREGATES.values())
            .join(Activity, JOIN.LEFT_OUTER)
            .group_by(User.id)
        )

    @staticmethod
    def apply_filters(
        query,
        *,
        before=None,
        after=None,
        game_id=None,
        platform_id=None,
    ):
        if after:
            query = query.where(Activity.timestamp >= after)

        if before:
            query = query.where(Activity.timestamp <= before)

        if game_id:
            query = query.where(Activity.game == game_id)

        if platform_id:
            query = query.where(Activity.platform == platform_id)

        return query

    @staticmethod
    def apply_sort(
        query,
        sort: SORTS_LITERAL,
        order: Literal["asc", "desc"] = "desc",
    ):
        column = UserQuery.SORTS[sort]
        return query.order_by(column.desc() if order == "desc" else column.asc())
