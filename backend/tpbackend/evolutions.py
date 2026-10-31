import logging
import os
from pathlib import Path

from peewee import PostgresqlDatabase

logger = logging.getLogger("evolutions")

EVOLUTIONS_DIR = Path(
    os.environ.get(
        "EVOLUTIONS_DIR", Path(__file__).resolve().parent.parent / "evolutions"
    )
)
LOCK_ID = 1337


def numbered(directory: Path) -> dict[int, Path]:
    out = {}
    for f in directory.glob("*.sql"):
        if f.stem.isdigit():
            out[int(f.stem)] = f
    return out


def to_apply(evolutions: dict[int, Path], current: int) -> list[tuple[int, Path]]:
    return [(n, evolutions[n]) for n in sorted(evolutions) if n > current]


def apply(database: str, **connect_params):
    db = PostgresqlDatabase(database, **connect_params)
    db.connect()
    try:
        db.execute_sql("SELECT pg_advisory_lock(%s)", (LOCK_ID,))
        db.execute_sql(
            "CREATE TABLE IF NOT EXISTS public.evolutions ("
            "id integer PRIMARY KEY, applied timestamptz NOT NULL DEFAULT now())"
        )
        current = db.execute_sql("SELECT max(id) FROM public.evolutions").fetchone()[0]
        if current is None:
            current = 0

        pending = to_apply(numbered(EVOLUTIONS_DIR), current)
        for n, path in pending:
            _run(db, n, path)

        after = db.execute_sql("SELECT max(id) FROM public.evolutions").fetchone()[0]
        if not after:
            raise ValueError("No evolutions applied?")
        logger.info("Database is up to date (evolution %d)", after)
    finally:
        db.close()


def _run(db: PostgresqlDatabase, n: int, path: Path):
    logger.info("Applying evolution %s", path.name)
    with db.atomic():
        db.cursor().execute(path.read_text())
        db.execute_sql("RESET ALL")
        db.execute_sql("INSERT INTO public.evolutions (id) VALUES (%s)", (n,))
    logger.info("Applied evolution %s successfully!", path.name)
