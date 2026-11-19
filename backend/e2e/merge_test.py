import datetime

from tpbackend.operations import merge_games
from tpbackend.storage import Activity, Game, LiveActivity

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

    def test_nsfw_source_makes_target_nsfw(self, make_game):
        target = make_game("Bla")
        source = make_game("Bla™", nsfw=True)

        merge_games(source, target)

        assert Game.get_by_id(target.get_id()).get_nsfw() is True

    def test_target_is_child_of_source(self, make_game):
        source = make_game("Parent")
        target = make_game("Child", parent=source)

        merge_games(source, target)

        target = Game.get_by_id(target.get_id())
        assert target.get_parent() is None
        assert "Parent" in target.get_aliases()
