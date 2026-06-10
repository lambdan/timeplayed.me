from fastapi import Query, Path


PATH_IDS_CSV = Path(
    description="Specify single ID, or multiple (separated by comma)",
    openapi_examples={
        "single": {"value": 1, "description": "Single ID"},
        "multiple": {"value": "1,2,3", "description": "Multiple IDs"},
    },
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
