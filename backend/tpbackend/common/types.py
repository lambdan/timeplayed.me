from fastapi import Query, Path
from typing import TypeAlias, Literal

AscDescOrder: TypeAlias = Literal["asc", "desc"]


QUERY_TS_BEFORE = Query(
    default=None,
    description="Timestamp (in milliseconds). Only include activities before this timestamp.",
)

QUERY_TS_AFTER = Query(
    default=None,
    description="Timestamp (in milliseconds). Only include activities after this timestamp.",
)
