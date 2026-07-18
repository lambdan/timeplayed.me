from pydantic import BaseModel
from tpbackend.utils2 import dt_to_ts
from tpbackend.common.models import BaseTotals


class GameStats(BaseTotals):
    user_count: int
    platform_count: int


class API_Game(BaseModel):
    id: int
    name: str
    sgdb_id: int | None
    sgdb_grid_id: int | None
    igdb_id: int | None
    image_url: str | None
    aliases: list[str]
    release_year: int | None
    created: int
    updated: int
    children_ids: list[int]
    parent_id: int | None

    @classmethod
    def from_game(cls, game):
        return cls(
            id=game.id,
            name=game.name,
            sgdb_id=game.sgdb_id,
            sgdb_grid_id=game.sgdb_grid_id,
            igdb_id=game.igdb_id,
            image_url=game.image_url,
            aliases=game.aliases,
            release_year=game.release_year,
            created=dt_to_ts(game.created),
            updated=dt_to_ts(game.updated),
            children_ids=[child.id for child in game.children],
            parent_id=game.parent_id,
        )


class API_GameWithStats(API_Game):
    stats: GameStats

    @classmethod
    def from_game(cls, game):
        return cls(
            id=game.id,
            name=game.name,
            sgdb_id=game.sgdb_id,
            sgdb_grid_id=game.sgdb_grid_id,
            igdb_id=game.igdb_id,
            image_url=game.image_url,
            aliases=game.aliases,
            release_year=game.release_year,
            created=dt_to_ts(game.created),
            updated=dt_to_ts(game.updated),
            children_ids=[child.id for child in game.children],
            parent_id=game.parent_id,
            stats=GameStats(
                seconds=game.total_seconds,
                activity_count=game.activity_count,
                user_count=game.user_count,
                platform_count=game.platform_count,
                last_activity=(
                    dt_to_ts(game.last_activity) if game.last_activity else None
                ),
                first_activity=(
                    dt_to_ts(game.first_activity) if game.first_activity else None
                ),
            ),
        )
