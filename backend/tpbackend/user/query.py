import logging
from typing import Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.storage import User, Activity

logger = logging.getLogger("user_query")


class UserQuery:
    SORTS = {
        "name": User.name,
        "id": User.id,
        "created": User.created,
        "updated": User.updated,
    }

    @staticmethod
    def base():
        return User.select()

    @staticmethod
    def apply_ids(
        query,
        user_ids: list[int],
    ):
        return query.where(User.id.in_(user_ids))  # type: ignore

    @staticmethod
    def apply_sort(query, sort, order):
        column = UserQuery.SORTS[sort]
        return query.order_by(
            column.desc(nulls="LAST") if order == "desc" else column.asc(nulls="LAST")
        )

    @staticmethod
    def search(query, search: str):
        if not search or search.strip() == "":
            return query
        q = query.where(User.search.contains(search.lower()))  # type: ignore
        return q


class UserStatsQuery:
    TOTAL_SECONDS = fn.SUM(
        Case(None, [(Activity.hidden == False, Activity.seconds)], 0)
    ).alias("total_seconds")

    ACTIVITY_COUNT = fn.COUNT(Case(None, [(Activity.hidden == False, 1)], None)).alias(
        "activity_count"
    )

    LAST_ACTIVITY = fn.MAX(
        Case(None, [(Activity.hidden == False, Activity.timestamp)], None)
    ).alias("last_activity")

    FIRST_ACTIVITY = fn.MIN(
        Case(None, [(Activity.hidden == False, Activity.timestamp)], None)
    ).alias("first_activity")

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
        "first_activity": FIRST_ACTIVITY,
        "game_count": GAME_COUNT,
        "platform_count": PLATFORM_COUNT,
    }

    SORTS = {
        **AGGREGATES,
        "name": User.name,
        "id": User.id,
    }

    @staticmethod
    def base():
        return (
            User.select(User, *UserStatsQuery.AGGREGATES.values())
            .join(Activity, JOIN.LEFT_OUTER)
            .group_by(User.id)
        )

    @staticmethod
    def apply_ids(
        query,
        user_ids: list[int],
    ):
        return query.where(User.id.in_(user_ids))  # type: ignore

    @staticmethod
    def apply_sort(query, sort, order):
        column = UserStatsQuery.SORTS[sort]
        return query.order_by(
            column.desc(nulls="LAST") if order == "desc" else column.asc(nulls="LAST")
        )
