import pytest
from peewee import PostgresqlDatabase

from conftest import DB_PORT
from tpbackend import evolutions
from tpbackend.storage import db as tp_db


def connect_params() -> dict:
    params = dict(tp_db.connect_params)
    params["port"] = DB_PORT
    return params


@pytest.fixture
def scratch_db():
    """an empty database next to the e2e one, dropped afterwards"""
    admin = PostgresqlDatabase("postgres", **connect_params())
    admin.connect()
    admin.execute_sql("DROP DATABASE IF EXISTS evolutions_scratch")
    admin.execute_sql("CREATE DATABASE evolutions_scratch")
    yield "evolutions_scratch"
    admin.execute_sql("DROP DATABASE evolutions_scratch WITH (FORCE)")
    admin.close()


class TestEvolutions:
    def test_backend_applied_everything_on_startup(self, db):
        newest = max(evolutions.numbered(evolutions.EVOLUTIONS_DIR))
        applied = tp_db.execute_sql("SELECT max(id) FROM evolutions").fetchone()[0]
        assert applied == newest
        # 2.sql dropped this
        columns = [c.name for c in tp_db.get_columns("game")]
        assert "sgdb_grid_id" not in columns
        # 3.sql dropped this, default permissions come from code
        permissions_default = tp_db.execute_sql(
            "SELECT column_default FROM information_schema.columns "
            "WHERE table_name = 'user' AND column_name = 'permissions'"
        ).fetchone()[0]
        assert permissions_default is None

    def test_running_again_does_nothing(self, db):
        before = tp_db.execute_sql("SELECT count(*) FROM evolutions").fetchone()[0]
        evolutions.apply(tp_db.database, **connect_params())
        after = tp_db.execute_sql("SELECT count(*) FROM evolutions").fetchone()[0]
        assert before == after

    def test_existing_tables_without_evolutions_table(self, scratch_db):
        # 1.sql fails on the existing table and is rolled back
        scratch = PostgresqlDatabase(scratch_db, **connect_params())
        scratch.execute_sql("CREATE TABLE game (id integer)")

        with pytest.raises(Exception, match="already exists"):
            evolutions.apply(scratch_db, **connect_params())

        assert scratch.execute_sql("SELECT count(*) FROM evolutions").fetchone()[0] == 0
        assert not scratch.table_exists("activity")
        scratch.close()

    def test_continues_from_recorded_evolution(self, scratch_db):
        # an existing database, told once that it's at evolution 1
        scratch = PostgresqlDatabase(scratch_db, **connect_params())
        # just what the evolutions after 1 touch
        scratch.execute_sql("CREATE TABLE game (id integer, sgdb_grid_id integer)")
        scratch.execute_sql(
            "CREATE TABLE \"user\" (id integer, permissions text[] DEFAULT '{commands}')"
        )
        scratch.execute_sql(
            "CREATE TABLE evolutions (id integer PRIMARY KEY, applied timestamptz NOT NULL DEFAULT now())"
        )
        scratch.execute_sql("INSERT INTO evolutions (id) VALUES (1)")
        scratch.execute_sql(
            "INSERT INTO \"user\" (id, permissions) VALUES (1, '{commands}'), (2, '{commands,show_name}'), (3, NULL)"
        )

        evolutions.apply(scratch_db, **connect_params())

        assert "sgdb_grid_id" not in [c.name for c in scratch.get_columns("game")]
        # 4.sql gave existing users show_avatar and show_name, once
        permissions = scratch.execute_sql(
            'SELECT permissions FROM "user" ORDER BY id'
        ).fetchall()
        assert [p[0] for p in permissions] == [
            ["commands", "show_avatar", "show_name"],
            ["commands", "show_name", "show_avatar"],
            ["show_avatar", "show_name"],
        ]
        newest = max(evolutions.numbered(evolutions.EVOLUTIONS_DIR))
        assert (
            scratch.execute_sql("SELECT max(id) FROM evolutions").fetchone()[0]
            == newest
        )
        scratch.close()
