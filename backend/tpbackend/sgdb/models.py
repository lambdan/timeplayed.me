from pydantic import BaseModel


class SGDB_Game(BaseModel):
    id: int
    name: str
    verified: bool
    release_date: float


class SGDB_Author(BaseModel):
    name: str | None
    steam64: str | None
    avatar: str | None


class SGDB_Grid(BaseModel):
    id: int | None
    score: int | None
    width: int | None
    height: int | None
    style: str | None
    mime: str | None
    language: str | None
    url: str | None
    thumb: str | None
    type: str | None
    author: SGDB_Author | None
    upvotes: int | None
    downvotes: int | None
