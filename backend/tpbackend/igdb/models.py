from pydantic import BaseModel


class IGDB_SearchResult(BaseModel):
    id: int
    first_release_date: int | None
    name: str
    url: str
