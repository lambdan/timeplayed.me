import logging
from typing import Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.common.query import sort_by
from tpbackend.permissions import Permission
from tpbackend.storage import User, Activity


def private_condition(viewer: User | None = None):
    """
    the private users, but the viewer. Private users' activity is only on their own
    user page, so pass the viewer only for routes that are about one user
    """
    private = User.permissions.contains(str(Permission.PRIVATE))  # type: ignore
    if viewer:
        private = private & (User.id != viewer.get_id())
    return private


def not_private_activity():
    """
    activity of users who aren't private. Private users' activity is only on their own
    user page, it's left out of everything else (totals, lists, charts...)
    """
    private_users = User.select(User.id).where(private_condition())
    return Activity.user.not_in(private_users)  # type: ignore


def anonymous_condition():
    """like User.is_anonymous"""
    return User.permissions.contains_any(  # type: ignore
        str(Permission.ANONYMOUS), str(Permission.FORCE_ANONYMOUS)
    )


logger = logging.getLogger("user_query")


# the name like API_User shows it, so sorting by name doesn't give away hidden names
SHOWN_NAME = Case(
    None,
    [(anonymous_condition(), fn.CONCAT("User ", User.id))],
    fn.COALESCE(User.display_name, User.name),
)


class UserQuery:
    SORTS = {
        "name": SHOWN_NAME,
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
        return sort_by(query, UserQuery.SORTS[sort], order)

    @staticmethod
    def search(query, search: str):
        if not search or search.strip() == "":
            return query
        q = query.where(User.search.contains(search.lower()))  # type: ignore
        return q

    @staticmethod
    def public_search(query, search: str):
        """search, but anonymous users' real names don't match"""
        if not search or search.strip() == "":
            return query
        query = UserQuery.search(query, search)
        return query.where(~anonymous_condition())

    @staticmethod
    def not_private(query, viewer: User | None = None):
        """leaves out private users, but the viewer"""
        return query.where(~private_condition(viewer))


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
        "name": SHOWN_NAME,
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
        return sort_by(query, UserStatsQuery.SORTS[sort], order)
