from pydantic import BaseModel


class IGDB_SearchResult(BaseModel):
    id: int
    first_release_date: int | None = None
    name: str
    url: str


class IGDB_Cover(BaseModel):
    id: int
    image_id: str


class IGDB_GameInfo(BaseModel):
    id: int
    name: str
    first_release_date: int | None = None
    url: str
    summary: str | None = None
    cover: IGDB_Cover | None = None
    # IGDB platform IDs (not same as ours)
    platforms: list[int] | None = None
    # IGDB Company IDs
    involved_companies: list[int] | None = None
