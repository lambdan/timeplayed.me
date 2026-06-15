from fastapi import Query, Path
from typing import Annotated, TypeAlias, Literal

AscDescOrder: TypeAlias = Literal["asc", "desc"]


def offset(default: int = 0):
    return Query(
        default=default,
        json_schema_extra={"type": "integer", "minimum": 0},
    )


def limit(default: int = 100, maximum: int = 100):
    return Query(
        default=default,
        json_schema_extra={"type": "integer", "minimum": 1, "maximum": maximum},
    )


def sorts(allowed: list[str], default: str | None = None):
    if not default:
        default = allowed[0]
    return Query(
        default=default,
        description="Sort by",
        json_schema_extra={"type": "string", "enum": allowed},
    )


########### QUERY #############


def query_csv(name: str, default=None):
    return Query(
        default=default,
        description=f"Comma-separated list of {name} to filter by",
        json_schema_extra={"type": "string"},
    )


def query_id(name: str, default=None):
    return Query(
        default=default,
        description=f"ID of the {name} to filter by",
        json_schema_extra={"type": "integer"},
    )


def query_ts(name: Literal["before", "after"]):
    return Query(
        default=None,
        description=f"Timestamp (in milliseconds). Only include activities {name} this timestamp.",
        json_schema_extra={"type": "integer", "format": "timestamp-millis"},
    )


def query_search(name: str):
    return Query(
        default=None,
        description=f"Search term to filter {name} by",
        json_schema_extra={"type": "string"},
    )


################## PATH ###################


def path_id(name: str):
    return Path(
        description=f"ID of the {name} to filter by",
        json_schema_extra={"type": "integer"},
    )


def path_csv(name: str):
    return Path(
        description=f"Comma-separated list of {name} to filter by",
        json_schema_extra={"type": "string"},
    )
