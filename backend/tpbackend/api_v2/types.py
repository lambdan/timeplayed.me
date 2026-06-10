from fastapi import Query, Path
from typing import TypeAlias, Literal

AscDescOrder: TypeAlias = Literal["asc", "desc"]

PATH_IDS_CSV = Path(
    description="Specify single ID, or multiple (separated by comma)",
)

QUERY_TS_BEFORE = Query(
    default=None,
    title="Before Timestamp",
    description="Timestamp (in milliseconds). Only include activities before this timestamp.",
)

QUERY_TS_AFTER = Query(
    default=None,
    title="After Timestamp",
    description="Timestamp (in milliseconds). Only include activities after this timestamp.",
)
