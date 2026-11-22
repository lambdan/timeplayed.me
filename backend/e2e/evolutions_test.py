import datetime

import pytest
from peewee import PostgresqlDatabase

from conftest import DB_PORT
from tpbackend import evolutions
from tpbackend.storage import (
    Game,
    History,
    ImageFile,
    ImageFileData,
    Platform,
    User,
)
from tpbackend.storage import db as tp_db
from tpbackend.utils2 import now


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
        scratch.execute_sql(
            "CREATE TABLE game (id integer PRIMARY KEY, sgdb_grid_id integer, sgdb_id integer, image_url varchar)"
        )
        scratch.execute_sql(
            "INSERT INTO game (id, image_url) VALUES (1, '-'), (2, 'http://x/a.png'), (3, NULL)"
        )
        scratch.execute_sql(
            "CREATE TABLE \"user\" (id integer PRIMARY KEY, name varchar, permissions text[] DEFAULT '{commands}', default_platform_id integer, pc_platform varchar DEFAULT 'win')"
        )
        scratch.execute_sql(
            "CREATE TABLE platform (id serial, abbreviation varchar UNIQUE, name varchar, icon varchar, search varchar)"
        )
        scratch.execute_sql(
            "CREATE TABLE history (id serial, timestamp timestamptz DEFAULT now(), game_id integer, user_id integer, platform_id integer, activity_id integer, message text)"
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
        # 5.sql dropped the default platform
        assert "default_platform_id" not in [
            c.name for c in scratch.get_columns("user")
        ]
        # 6.sql turned image_url '-' into cover_disabled
        games = scratch.execute_sql(
            "SELECT cover_disabled FROM game ORDER BY id"
        ).fetchall()
        assert games == [(True,), (False,), (False,)]
        # 9.sql dropped SteamGridDB and image urls
        game_columns = [c.name for c in scratch.get_columns("game")]
        assert "sgdb_id" not in game_columns
        assert "image_url" not in game_columns
        # 7.sql, nothing is nsfw until marked
        assert (
            scratch.execute_sql("SELECT count(*) FROM game WHERE nsfw").fetchone()[0]
            == 0
        )
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


class TestEvolution11:
    """removes versions that are copies of an original small enough to be them"""

    def image(self, content_type="image/jpeg", size=(264, 352), **kwargs) -> ImageFile:
        image = ImageFile.create(
            content_type=content_type,
            size=1,
            sha256="x",
            width=size[0],
            height=size[1],
            **kwargs,
        )
        ImageFileData.create(file=image.get_id(), data=b"x")
        return image

    def versions(self, original: ImageFile) -> list[str]:
        rows = ImageFile.select().where(ImageFile.original == original.get_id())
        return sorted(r.get_version() for r in rows)

    def test_removes_copies(self, db):
        def versions_of(original):
            for name, size in [
                ("display", (264, 352)),
                ("thumbnail", (120, 160)),
                ("preview", (8, 11)),
            ]:
                self.image(size=size, original=original.get_id(), version=name)

        igdb = self.image()
        versions_of(igdb)
        large = self.image(size=(1200, 1800))
        versions_of(large)
        gif = self.image("image/gif")
        versions_of(gif)

        sql = (evolutions.EVOLUTIONS_DIR / "11.sql").read_text()
        tp_db.execute_sql(sql)

        assert self.versions(igdb) == ["preview", "thumbnail"]
        assert self.versions(large) == ["display", "preview", "thumbnail"]
        assert self.versions(gif) == ["display", "preview", "thumbnail"]
        # the bytes went with them
        assert ImageFileData.select().count() == ImageFile.select().count()


class TestEvolution12:
    """adds the pc platform, users who never picked a pc platform go from win to it"""

    def test_moves_users_who_never_changed_it(self, db):
        never_changed = User.create(name="never", pc_platform="win")
        changed_back = User.create(name="changed_back", pc_platform="win")
        changed_back.set_pc_platform("linux")
        changed_back.set_pc_platform("win")
        changed_back.save()
        on_mac = User.create(name="mac", pc_platform="mac")

        # like the evolutions runner, execute_sql would trip on the % in LIKE
        tp_db.cursor().execute((evolutions.EVOLUTIONS_DIR / "12.sql").read_text())

        assert User.get_by_id(never_changed.get_id()).get_pc_platform() == "pc"
        assert User.get_by_id(changed_back.get_id()).get_pc_platform() == "win"
        assert User.get_by_id(on_mac.get_id()).get_pc_platform() == "mac"
        assert History.select().where(History.user == never_changed).count() == 1

        pc = Platform.get(Platform.abbreviation == "pc")
        assert pc.get_name() == "PC"
        # new users get it too
        assert User.create(name="new").get_pc_platform() == "pc"


class TestEvolution13:
    """history gets an actor, backfilled from messages that named the admin"""

    def history(self, message: str, seconds_ago: float = 0, **about) -> History:
        timestamp = now() - datetime.timedelta(seconds=seconds_ago)
        return History.create(message=message, timestamp=timestamp, **about)

    def run(self):
        tp_db.cursor().execute((evolutions.EVOLUTIONS_DIR / "13.sql").read_text())

    def test_edited_by_admin(self, db):
        admin = User.create(name="djs")
        game = Game.create(name="TitaniumRP")
        other = Game.create(name="Other")
        created = self.history("Created during Oblivionis sync", 300, game=game)
        parent = self.history(
            "Parent changed from None to 'FiveM' (9)", 0.01, game=game
        )
        name = self.history("Name changed from 'a' to 'b'", 0.01, game=game)
        not_this_game = self.history("Name changed", 0.01, game=other)
        edited = self.history("Edited by admin djs", game=game)

        self.run()

        def actor(h: History):
            return History.get_by_id(h.get_id()).get_actor()

        assert actor(parent) == admin
        assert actor(name) == admin
        assert actor(created) is None
        assert actor(not_this_game) is None
        assert actor(edited) == admin

    def test_other_messages(self, db):
        admin = User.create(name="djs")
        bob = User.create(name="bob")
        added = self.history("User added by admin djs", user=bob)
        revoked = self.history("Revoked 2 tokens (admin djs)", user=bob)
        token = self.history("Token ab...cd generated by admin djs", user=bob)
        sgdb = self.history(
            f"Game added by SGDB ID by user {admin.get_id()}",
            game=Game.create(name="x"),
        )

        igdb = self.history(
            f"Game added by IGDB ID by user {admin.get_id()}",
            game=Game.create(name="y"),
        )

        self.run()

        for h in [added, revoked, token, sgdb, igdb]:
            assert History.get_by_id(h.get_id()).get_actor() == admin
        # messages are kept as they were
        assert History.get_by_id(added.get_id()).message == "User added by admin djs"

    def test_unknown_or_ambiguous_name_is_left_alone(self, db):
        User.create(name="twice")
        User.create(name="twice")
        bob = User.create(name="bob")
        gone = self.history("User added by admin someone", user=bob)
        ambiguous = self.history("Permissions set by admin twice", user=bob)

        self.run()

        for h in [gone, ambiguous]:
            assert History.get_by_id(h.get_id()).get_actor() is None
