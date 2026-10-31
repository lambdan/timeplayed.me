import datetime

from discord_test import FakeAuthor, FakeMessage
from tpbackend.discord.bot import dm_receive
from tpbackend.operations import merge_games
from tpbackend.storage import Activity, Game, LiveActivity, User

UTC = datetime.timezone.utc


def add_activity(user, game, platform, seconds=3600):
    return Activity.create(
        user=user,
        game=game,
        platform=platform,
        seconds=seconds,
        timestamp=datetime.datetime.now(UTC),
    )


class TestMergeGames:
    def test_moves_everything_and_deletes_source(
        self, make_user, make_game, make_platform
    ):
        alice, _ = make_user(name="alice")
        bob, _ = make_user(name="bob")
        pc = make_platform("pc")
        target = make_game("Bla", igdb_id=1234)
        source = make_game("Bla™", aliases=["Bla (beta)"], steam_id=999)
        child = make_game("Bla DLC", parent=source)
        add_activity(alice, source, pc)
        add_activity(bob, source, pc)
        add_activity(alice, target, pc)
        LiveActivity.create(
            user=bob, game=source, platform=pc, started=datetime.datetime.now(UTC)
        )

        moved = merge_games(source, target)

        assert moved == 2
        assert Game.get_or_none(Game.id == source.get_id()) is None
        target = Game.get_by_id(target.get_id())
        assert Activity.select().where(Activity.game == target).count() == 3
        assert LiveActivity.get().get_game() == target
        assert Game.get_by_id(child.get_id()).get_parent() == target
        assert set(target.get_aliases()) == {"Bla™", "Bla (beta)"}
        # target didn't have a steam id, so it gets the sources
        assert target.steam_id == 999
        assert any("Merged in 'Bla™'" in h for h in target.get_history())

    def test_target_is_child_of_source(self, make_game):
        source = make_game("Parent")
        target = make_game("Child", parent=source)

        merge_games(source, target)

        target = Game.get_by_id(target.get_id())
        assert target.get_parent() is None
        assert "Parent" in target.get_aliases()


class TestIGDBCommandMerge:
    def test_preview_then_merge(self, make_game, make_platform):
        User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )
        pc = make_platform("pc")
        target = make_game("Bla", igdb_id=1234)
        source = make_game("Bla™")
        add_activity(User.get(), source, pc)
        cmd = f"!igdb {source.get_id()} 1234"

        # without y: only tells what would happen
        reply = dm_receive(FakeMessage(cmd, FakeAuthor()))  # type: ignore
        assert reply and "Run the command again with `y`" in reply
        assert Game.get_or_none(Game.id == source.get_id()) is not None

        reply = dm_receive(FakeMessage(cmd + " y", FakeAuthor()))  # type: ignore
        assert reply and reply.startswith("Merged")
        assert Game.get_or_none(Game.id == source.get_id()) is None
        target = Game.get_by_id(target.get_id())
        assert "Bla™" in target.get_aliases()
        assert Activity.get().get_game() == target


class TestMergeCommand:
    def test_preview_then_merge(self, make_game, make_platform):
        User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )
        pc = make_platform("pc")
        target = make_game("Bla")
        source = make_game("Bla™")
        add_activity(User.get(), source, pc)
        cmd = f"!merge {source.get_id()} {target.get_id()}"

        reply = dm_receive(FakeMessage(cmd, FakeAuthor()))  # type: ignore
        assert reply and "Run the command again with `y`" in reply
        assert Game.get_or_none(Game.id == source.get_id()) is not None

        reply = dm_receive(FakeMessage(cmd + " y", FakeAuthor()))  # type: ignore
        assert reply and reply.startswith("Merged")
        assert Game.get_or_none(Game.id == source.get_id()) is None
        assert "Bla™" in Game.get_by_id(target.get_id()).get_aliases()
        assert Activity.get().get_game() == target

    def test_same_name_doesnt_add_alias(self, make_game):
        User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )
        target = make_game("Grand Theft Auto: Vice City")
        source = make_game("Grand Theft Auto: Vice City")
        cmd = f"!merge {source.get_id()} {target.get_id()}"

        reply = dm_receive(FakeMessage(cmd, FakeAuthor()))  # type: ignore
        assert reply and "alias" not in reply
        reply = dm_receive(FakeMessage(cmd + " y", FakeAuthor()))  # type: ignore
        assert reply and reply.startswith("Merged") and "alias" not in reply
        assert Game.get_by_id(target.get_id()).get_aliases() == []

    def test_admin_only(self, make_game):
        User.create(discord_id="1234", name="discordguy", permissions=["commands"])
        source = make_game("Bla™")
        target = make_game("Bla")

        dm_receive(FakeMessage(f"!merge {source.get_id()} {target.get_id()} y", FakeAuthor()))  # type: ignore
        assert Game.get_or_none(Game.id == source.get_id()) is not None

    def test_errors(self, make_game):
        User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )
        game = make_game("Bla")
        reply = dm_receive(FakeMessage(f"!merge {game.get_id()} {game.get_id()} y", FakeAuthor()))  # type: ignore
        assert reply and "itself" in reply
        reply = dm_receive(FakeMessage(f"!merge 9999 {game.get_id()}", FakeAuthor()))  # type: ignore
        assert reply and "not found" in reply
