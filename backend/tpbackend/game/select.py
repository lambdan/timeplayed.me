import logging

from tpbackend.storage import Game
from tpbackend.game.query import GameQuery
from peewee import fn

logger = logging.getLogger("game_select")


class GameSelect:
    @staticmethod
    def by_id(game_id: int | str) -> Game | None:
        return Game.get_or_none(Game.id == int(game_id))  # type: ignore

    @staticmethod
    def by_name(name: str, case_sensitive=False) -> Game | None:
        # sort by release year (null last)
        base = GameQuery.base(include_hidden=True)
        if case_sensitive:
            query = base.where(Game.name == name)  # type: ignore
        else:
            query = base.where(fn.LOWER(Game.name) == name.lower())  # type: ignore
        # sort by release year
        # (because in theory if it shows up in Discord, it should be a newer game,
        # eg RE2 1998 vs RE2 remake 2019)
        query = GameQuery.apply_sort(query, "release_year", "desc")
        return query.first()

    @staticmethod
    def by_alias(alias: str) -> Game | None:
        # aliases are case sensitive, so no need to lowercase the input
        base = GameQuery.base(include_hidden=True)
        return base.where(Game.aliases.contains(alias)).first()  # type: ignore

    @staticmethod
    def by_name_or_alias(s: str) -> Game | None:
        game = GameSelect.by_name(s, case_sensitive=True)
        if game:
            logger.info("Found game by name: '%s' (id: %s)", s, game.id)
            return game
        # any game with this alias?
        game = GameSelect.by_alias(s)
        if game:
            logger.info("Found game by alias '%s': '%s' (id: %s)", s, game.name, game.id)  # type: ignore
            return game
        # any game with this name but different capitalization?
        game = GameSelect.by_name(s, case_sensitive=False)
        if game:
            logger.info(
                "Found game by different capitalization: db: '%s' / s: '%s' (id: %s)",
                game.name,
                s,
                game.id,
            )
            return game
        return None

    @staticmethod
    def by_name_and_year(name: str, release_year: int | None) -> Game | None:
        base = GameQuery.base(include_hidden=True)
        if release_year is None:
            query = base.where(
                (Game.name == name) & (Game.release_year.is_null())  # type: ignore
            )
        else:
            query = base.where(
                (Game.name == name) & (Game.release_year == release_year)  # type: ignore
            )
        return query.first()
