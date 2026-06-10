import datetime
import logging
from typing import Literal

from tpbackend.storage.storage_v2 import Activity

logger = logging.getLogger("activities_query")


class ActivityQuery:
    SORTS = {
        "id": Activity.id,
        "timestamp": Activity.timestamp,
    }

    SORTS_LITERAL = Literal["id", "timestamp"]

    @staticmethod
    def base(include_hidden=False):
        if include_hidden:
            return Activity.select()
        else:
            return Activity.select().where(Activity.hidden == False)  # noqa: E712

    @staticmethod
    def apply_sort(
        query,
        sort: SORTS_LITERAL,
        order: Literal["asc", "desc"] = "desc",
    ):
        column = ActivityQuery.SORTS[sort]
        return query.order_by(column.desc() if order == "desc" else column.asc())

    @staticmethod
    def id(query, activity_id: int):
        return query.where(Activity.id == activity_id)  # type: ignore

    @staticmethod
    def ids(
        query,
        activity_ids: list[int],
    ):
        return query.where(Activity.id.in_(activity_ids))  # type: ignore

    @staticmethod
    def user(query, user_id: int):
        return query.where(Activity.user == user_id)  # type: ignore

    @staticmethod
    def users(
        query,
        user_ids: list[int],
    ):
        return query.where(Activity.user.in_(user_ids))  # type: ignore

    @staticmethod
    def game(query, game_id: int):
        return query.where(Activity.game == game_id)  # type: ignore

    @staticmethod
    def games(
        query,
        game_ids: list[int],
    ):
        return query.where(Activity.game.in_(game_ids))  # type: ignore

    @staticmethod
    def platform(query, platform_id: int):
        return query.where(Activity.platform == platform_id)  # type: ignore

    @staticmethod
    def platforms(
        query,
        platform_ids: list[int],
    ):
        return query.where(Activity.platform.in_(platform_ids))  # type: ignore

    @staticmethod
    def before(query, before: int | datetime.datetime):
        if isinstance(before, int):
            before = datetime.datetime.fromtimestamp(before)
            if before.year > 10000:  # probably ms instead of s
                before = datetime.datetime.fromtimestamp(before.timestamp() / 1000)
        return query.where(Activity.timestamp <= before)  # type: ignore

    @staticmethod
    def after(query, after: int | datetime.datetime):
        dt = None
        if isinstance(after, int):
            divide = 1000 if after > 10**12 else 1
            dt = datetime.datetime.fromtimestamp(after / divide)
        else:
            dt = after
        return query.where(Activity.timestamp >= dt)  # type: ignore

    @staticmethod
    def count(query) -> int:
        logger.info("Counting query: %s", query.sql())
        res = query.count()
        logger.info("Count result: %d", res)
        return res
