import logging
from typing import Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.storage import Activity, Platform

logger = logging.getLogger("platform_query")


class PlatformQuery:
    SORTS = {
        "name": Platform.name,
        "id": Platform.id,
        "created": Platform.created,
        "updated": Platform.updated,
    }

    @staticmethod
    def base():
        return Platform.select()

    @staticmethod
    def apply_ids(
        query,
        platform_ids: list[int],
    ):
        return query.where(Platform.id.in_(platform_ids))  # type: ignore

    @staticmethod
    def apply_sort(query, sort, order):
        column = PlatformQuery.SORTS[sort]
        return query.order_by(
            column.desc(nulls="LAST") if order == "desc" else column.asc(nulls="LAST")
        )

    @staticmethod
    def search(query, search: str):
        if not search or search.strip() == "":
            return query
        q = query.where(Platform.search.contains(search.lower()))  # type: ignore
        return q


class PlatformStatsQuery:
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

    USER_COUNT = fn.COUNT(
        fn.DISTINCT(Case(None, [(Activity.hidden == False, Activity.user)], None))
    ).alias("user_count")

    GAME_COUNT = fn.COUNT(
        fn.DISTINCT(Case(None, [(Activity.hidden == False, Activity.game)], None))
    ).alias("game_count")

    AGGREGATES = {
        "playtime": TOTAL_SECONDS,
        "activity_count": ACTIVITY_COUNT,
        "last_activity": LAST_ACTIVITY,
        "first_activity": FIRST_ACTIVITY,
        "user_count": USER_COUNT,
        "game_count": GAME_COUNT,
    }

    SORTS = {
        **AGGREGATES,
        "name": Platform.name,
        "id": Platform.id,
    }

    @staticmethod
    def base():
        return (
            Platform.select(Platform, *PlatformStatsQuery.AGGREGATES.values())
            .join(Activity, JOIN.LEFT_OUTER)
            .group_by(Platform.id)
        )

    @staticmethod
    def apply_ids(
        query,
        platform_ids: list[int],
    ):
        return query.where(Platform.id.in_(platform_ids))  # type: ignore

    @staticmethod
    def apply_sort(
        query,
        sort,
        order,
    ):
        column = PlatformStatsQuery.SORTS[sort]
        return query.order_by(
            column.desc(nulls="LAST") if order == "desc" else column.asc(nulls="LAST")
        )
