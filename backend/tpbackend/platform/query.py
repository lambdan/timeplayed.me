import logging
from typing import Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.common.query import sort_by
from tpbackend.user.query import not_private_activity
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
        return sort_by(query, PlatformQuery.SORTS[sort], order)

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
    def activity_join(platform_id, private: bool):
        """
        the activity to join for the platform id. private: also private users' activity,
        only for when it's filtered to one user (who can see it)
        """
        on = Activity.platform == platform_id
        if not private:
            on = on & not_private_activity()
        return on

    @staticmethod
    def base(private=False):
        return (
            Platform.select(Platform, *PlatformStatsQuery.AGGREGATES.values())
            .join(
                Activity,
                JOIN.LEFT_OUTER,
                on=PlatformStatsQuery.activity_join(Platform.id, private),
            )
            .group_by(Platform.id)
        )

    @staticmethod
    def family():
        """
        CTE with (root_id, platform_id) rows: every platform paired with itself and all
        its children, at any depth. UNION (not UNION ALL) so it ends even if parents loop
        """
        family = Platform.select(
            Platform.id.alias("root_id"), Platform.id.alias("platform_id")
        ).cte("platform_family", recursive=True, columns=("root_id", "platform_id"))
        child = Platform.alias()
        children = child.select(family.c.root_id, child.id).join(
            family, on=(child.parent == family.c.platform_id)
        )
        return family.union(children)

    @staticmethod
    def family_ids(platform_id: int):
        """
        Subquery with the ids of a platform and all its children (any depth)
        """
        family = PlatformStatsQuery.family()
        return family.select_from(family.c.platform_id).where(
            family.c.root_id == platform_id
        )

    @staticmethod
    def base_with_children(private=False):
        """
        Like base(), but the stats of every platform include all its children (any depth)
        """
        family = PlatformStatsQuery.family()
        return (
            Platform.select(Platform, *PlatformStatsQuery.AGGREGATES.values())
            .join(family, JOIN.LEFT_OUTER, on=(family.c.root_id == Platform.id))
            .join(
                Activity,
                JOIN.LEFT_OUTER,
                on=PlatformStatsQuery.activity_join(family.c.platform_id, private),
            )
            .group_by(Platform.id)
            .with_cte(family)
        )

    @staticmethod
    def top_level(query):
        """
        Only platforms without a parent
        """
        return query.where(Platform.parent.is_null())  # type: ignore

    @staticmethod
    def apply_ids(
        query,
        platform_ids: list[int],
    ):
        return query.where(Platform.id.in_(platform_ids))  # type: ignore

    @staticmethod
    def apply_sort(query, sort, order):
        return sort_by(query, PlatformStatsQuery.SORTS[sort], order)
