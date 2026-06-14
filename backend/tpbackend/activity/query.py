import datetime
import logging
from typing import Literal

from tpbackend.storage import Activity, User, Game, Platform
from tpbackend.utils2 import assertTimezone, validateTS, ts_to_dt

logger = logging.getLogger("activities_query")


class ActivityQuery:
    SORTS = {
        "id": Activity.id,
        "timestamp": Activity.timestamp,
    }

    @staticmethod
    def base(include_hidden=False):
        if include_hidden:
            return Activity.select()
        else:
            return Activity.select().where(Activity.hidden == False)  # noqa: E712

    @staticmethod
    def apply_sort(query, sort, order):
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
    def user(query, user: int | User):
        return query.where(Activity.user == user)  # type: ignore

    @staticmethod
    def users(
        query,
        user_ids: list[int],
    ):
        return query.where(Activity.user.in_(user_ids))  # type: ignore

    @staticmethod
    def game(query, game: int | Game):
        return query.where(Activity.game == game)  # type: ignore

    @staticmethod
    def games(
        query,
        game_ids: list[int],
    ):
        return query.where(Activity.game.in_(game_ids))  # type: ignore

    @staticmethod
    def platform(query, platform: int | Platform):
        return query.where(Activity.platform == platform)  # type: ignore

    @staticmethod
    def platforms(
        query,
        platform_ids: list[int],
    ):
        return query.where(Activity.platform.in_(platform_ids))  # type: ignore

    @staticmethod
    def before(query, before: int | datetime.datetime):
        if isinstance(before, int):
            before = ts_to_dt(before)
        dt = assertTimezone(before)
        return query.where(Activity.timestamp <= dt)  # type: ignore

    @staticmethod
    def after(query, after: int | datetime.datetime):
        if isinstance(after, int):
            after = ts_to_dt(after)
        dt = assertTimezone(after)
        return query.where(Activity.timestamp >= dt)  # type: ignore

    @staticmethod
    def count(query) -> int:
        logger.info("Counting query: %s", query.sql())
        res = query.count()
        logger.info("Count result: %d", res)
        return res
