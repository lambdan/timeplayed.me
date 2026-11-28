import logging
from typing import Literal

from peewee import (
    JOIN,
    fn,
    Case,
)
from tpbackend.common.query import sort_by
from tpbackend.user.query import not_private_activity
from tpbackend.storage import Activity, Game

logger = logging.getLogger("game_query")


class GameQuery:
    SORTS = {
        "name": Game.name,
        "id": Game.id,
        "created": Game.created,
        "updated": Game.updated,
        "release_year": Game.release_year,
    }

    @staticmethod
    def base(include_hidden=False):
        if include_hidden:
            return Game.select()
        else:
            return Game.select().where(Game.hidden == False)  # noqa: E712

    @staticmethod
    def apply_ids(
        query,
        game_ids: list[int],
    ):
        return query.where(Game.id.in_(game_ids))  # type: ignore

    @staticmethod
    def apply_sort(query, sort, order):
        return sort_by(query, GameQuery.SORTS[sort], order)

    @staticmethod
    def search(query, search: str):
        if not search or search.strip() == "":
            return query
        q = query.where(Game.search.contains(search.lower()))  # type: ignore
        # logger.debug(f"GameQuery search: {q.sql()}")
        return q

    @staticmethod
    def release_year(query, release_year: int | None):
        if release_year:
            return query.where(Game.release_year == release_year)  # type: ignore
        return query.where(Game.release_year.is_null())  # type: ignore


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

    FIRST_ACTIVITY = fn.MIN(
        Case(None, [(Activity.hidden == False, Activity.timestamp)], None)
    ).alias("first_activity")

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
        "first_activity": FIRST_ACTIVITY,
        "user_count": USER_COUNT,
        "platform_count": PLATFORM_COUNT,
    }

    SORTS = {
        **AGGREGATES,
        "name": Game.name,
        "id": Game.id,
    }

    @staticmethod
    def activity_join(game_id, private: bool):
        """
        the activity to join for the game id. private: also private users' activity,
        only for when it's filtered to one user (who can see it)
        """
        on = Activity.game == game_id
        if not private:
            on = on & not_private_activity()
        return on

    @staticmethod
    def base(include_hidden=False, private=False):
        query = (
            Game.select(Game, *GameStatsQuery.AGGREGATES.values())
            .join(
                Activity,
                JOIN.LEFT_OUTER,
                on=GameStatsQuery.activity_join(Game.id, private),
            )
            .group_by(Game.id)
        )
        if not include_hidden:
            query = query.where(Game.hidden == False)  # noqa: E712
        return query

    @staticmethod
    def family():
        """
        CTE with (root_id, game_id) rows: every game paired with itself and all its
        children, at any depth. UNION (not UNION ALL) so it ends even if parents loop
        """
        family = Game.select(Game.id.alias("root_id"), Game.id.alias("game_id")).cte(
            "family", recursive=True, columns=("root_id", "game_id")
        )
        child = Game.alias()
        children = child.select(family.c.root_id, child.id).join(
            family, on=(child.parent == family.c.game_id)
        )
        return family.union(children)

    @staticmethod
    def family_ids(game_id: int):
        """
        Subquery with the ids of a game and all its children (any depth)
        """
        family = GameStatsQuery.family()
        return family.select_from(family.c.game_id).where(family.c.root_id == game_id)

    @staticmethod
    def base_with_children(include_hidden=False, private=False):
        """
        Like base(), but the stats of every game include all its children (any depth)
        """
        family = GameStatsQuery.family()
        query = (
            Game.select(Game, *GameStatsQuery.AGGREGATES.values())
            .join(family, JOIN.LEFT_OUTER, on=(family.c.root_id == Game.id))
            .join(
                Activity,
                JOIN.LEFT_OUTER,
                on=GameStatsQuery.activity_join(family.c.game_id, private),
            )
            .group_by(Game.id)
            .with_cte(family)
        )
        if not include_hidden:
            query = query.where(Game.hidden == False)  # noqa: E712
        return query

    @staticmethod
    def top_level(query):
        """
        Only games without a parent
        """
        return query.where(Game.parent.is_null())  # type: ignore

    @staticmethod
    def apply_ids(
        query,
        game_ids: list[int],
    ):
        return query.where(Game.id.in_(game_ids))  # type: ignore

    @staticmethod
    def apply_sort(query, sort, order):
        return sort_by(query, GameStatsQuery.SORTS[sort], order)
