import logging
from typing import Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.storage.storage_v2 import Activity, Game

logger = logging.getLogger("game_query")


class GameQuery:
    SORTS = {
        "name": Game.name,
        "id": Game.id,
        "created": Game.created,
        "updated": Game.updated,
    }

    SORTS_LITERAL = Literal["name", "id", "created", "updated"]

    @staticmethod
    def base():
        return Game.select()

    @staticmethod
    def apply_ids(
        query,
        game_ids: list[int],
    ):
        return query.where(Game.id.in_(game_ids))  # type: ignore

    @staticmethod
    def apply_sort(
        query,
        sort: SORTS_LITERAL,
        order: Literal["asc", "desc"] = "desc",
    ):
        column = GameQuery.SORTS[sort]
        return query.order_by(column.desc() if order == "desc" else column.asc())


class GameStatsQuery:
    TOTAL_SECONDS = fn.SUM(
        Case(None, [(Activity.hidden == False, Activity.seconds)], 0)
    ).alias("total_seconds")

    ACTIVITY_COUNT = fn.COUNT(Case(None, [(Activity.hidden == False, 1)], None)).alias(
        "activity_count"
    )

    LAST_ACTIVITY = fn.MAX(
        Case(None, [(Activity.hidden == False, Activity.timestamp)], None)
    ).alias("last_activity")

    USER_COUNT = fn.COUNT(
        fn.DISTINCT(Case(None, [(Activity.hidden == False, Activity.user)], None))
    ).alias("user_count")

    PLATFORM_COUNT = fn.COUNT(
        fn.DISTINCT(Case(None, [(Activity.hidden == False, Activity.platform)], None))
    ).alias("platform_count")

    AGGREGATES = {
        "playtime": TOTAL_SECONDS,
        "activity_count": ACTIVITY_COUNT,
        "last_activity": LAST_ACTIVITY,
        "user_count": USER_COUNT,
        "platform_count": PLATFORM_COUNT,
    }

    SORTS = {
        **AGGREGATES,
        "name": Game.name,
        "id": Game.id,
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
            Game.select(Game, *GameStatsQuery.AGGREGATES.values())
            .join(Activity, JOIN.LEFT_OUTER)
            .group_by(Game.id)
        )

    @staticmethod
    def apply_ids(
        query,
        game_ids: list[int],
    ):
        return query.where(Game.id.in_(game_ids))  # type: ignore

    @staticmethod
    def apply_sort(
        query,
        sort: SORTS_LITERAL,
        order: Literal["asc", "desc"] = "desc",
    ):
        column = GameStatsQuery.SORTS[sort]
        return query.order_by(column.desc() if order == "desc" else column.asc())
