import datetime

from discord_test import FakeAuthor, FakeMessage
from tpbackend.discord.bot import dm_receive
from tpbackend.operations import (
    add_session,
    find_overlapping_groups,
    merge_overlapping_group,
)
from tpbackend.storage import Activity, User

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


def add_activity(user, game, platform, ended_minutes_ago, seconds):
    return Activity.create(
        user=user,
        game=game,
        platform=platform,
        seconds=seconds,
        timestamp=NOW - datetime.timedelta(minutes=ended_minutes_ago),
    )


class TestFindOverlappingGroups:
    def test_short_sessions_inside_long_one(self, make_user, make_game, make_platform):
        user, _ = make_user()
        game = make_game()
        pc = make_platform("pc")
        long = add_activity(user, game, pc, 0, 3600)
        short1 = add_activity(user, game, pc, 50, 60)
        short2 = add_activity(user, game, pc, 10, 60)
        # before the long one started, not part of the group
        add_activity(user, game, pc, 120, 60)

        groups = find_overlapping_groups()

        assert len(groups) == 1
        assert {a.get_id() for a in groups[0]} == {
            long.get_id(),
            short1.get_id(),
            short2.get_id(),
        }

    def test_chained_overlaps_are_one_group(self, make_user, make_game, make_platform):
        user, _ = make_user()
        game = make_game()
        pc = make_platform("pc")
        # 0-20, 15-35, 30-50 minutes ago: each overlaps the next
        add_activity(user, game, pc, 0, 20 * 60)
        add_activity(user, game, pc, 15, 20 * 60)
        add_activity(user, game, pc, 30, 20 * 60)

        groups = find_overlapping_groups()

        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_different_game_platform_or_user_dont_overlap(
        self, make_user, make_game, make_platform
    ):
        alice, _ = make_user(name="alice")
        bob, _ = make_user(name="bob")
        game = make_game("Bla")
        other_game = make_game("Other")
        pc = make_platform("pc")
        ps5 = make_platform("ps5")
        add_activity(alice, game, pc, 0, 3600)
        add_activity(alice, other_game, pc, 10, 60)
        add_activity(alice, game, ps5, 10, 60)
        add_activity(bob, game, pc, 10, 60)

        assert find_overlapping_groups() == []

    def test_back_to_back_sessions_overlap(self, make_user, make_game, make_platform):
        user, _ = make_user()
        game = make_game()
        pc = make_platform("pc")
        # first one ends exactly when the second one starts
        add_activity(user, game, pc, 0, 600)
        add_activity(user, game, pc, 10, 600)

        groups = find_overlapping_groups()

        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_sessions_with_a_gap_dont_overlap(
        self, make_user, make_game, make_platform
    ):
        user, _ = make_user()
        game = make_game()
        pc = make_platform("pc")
        # 0-10 and 11-21 minutes ago
        add_activity(user, game, pc, 0, 600)
        add_activity(user, game, pc, 11, 600)

        assert find_overlapping_groups() == []


class TestMergeOverlappingGroup:
    def test_keeps_longest_and_spans_whole_group(
        self, make_user, make_game, make_platform
    ):
        user, _ = make_user()
        game = make_game()
        pc = make_platform("pc")
        # 0-20, 15-35, 30-50 minutes ago
        add_activity(user, game, pc, 0, 20 * 60)
        longest = add_activity(user, game, pc, 15, 21 * 60)
        add_activity(user, game, pc, 30, 20 * 60)

        merged = merge_overlapping_group(find_overlapping_groups()[0])

        assert merged.get_id() == longest.get_id()
        assert Activity.select().count() == 1
        merged = Activity.get_by_id(merged.get_id())
        assert merged.get_ended() == NOW
        assert merged.get_seconds() == 50 * 60

    def test_long_session_containing_others_is_unchanged(
        self, make_user, make_game, make_platform
    ):
        user, _ = make_user()
        game = make_game()
        pc = make_platform("pc")
        long = add_activity(user, game, pc, 0, 3600)
        short = add_activity(user, game, pc, 10, 60)

        merge_overlapping_group(find_overlapping_groups()[0])

        merged = Activity.get_by_id(long.get_id())
        assert merged.get_seconds() == 3600
        assert merged.get_ended() == NOW
        assert any(
            f"overlapped activity id {short.get_id()}" in h
            for h in merged.get_history()
        )


class TestMergeOverlapsCommand:
    def test_preview_then_merge(self, make_game, make_platform):
        admin = User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )
        game = make_game()
        pc = make_platform("pc")
        long = add_activity(admin, game, pc, 0, 3600)
        short = add_activity(admin, game, pc, 10, 60)

        reply = dm_receive(FakeMessage("!merge_overlaps", FakeAuthor()))  # type: ignore
        assert reply
        assert f"keep #{long.get_id()}, remove #{short.get_id()}" in reply
        assert Activity.select().count() == 2

        reply = dm_receive(FakeMessage("!merge_overlaps y", FakeAuthor()))  # type: ignore
        assert reply
        assert "1 activities removed" in reply
        assert Activity.select().count() == 1

    def test_nothing_to_merge(self):
        User.create(
            discord_id="1234",
            name="discordguy",
            permissions=["commands", "admin"],
        )

        reply = dm_receive(FakeMessage("!merge_overlaps", FakeAuthor()))  # type: ignore
        assert reply == "No overlapping activities found."

    def test_admin_only(self, make_game, make_platform):
        regular = User.create(
            discord_id="1234", name="discordguy", permissions=["commands"]
        )
        game = make_game()
        pc = make_platform("pc")
        add_activity(regular, game, pc, 0, 3600)
        add_activity(regular, game, pc, 10, 60)

        dm_receive(FakeMessage("!merge_overlaps y", FakeAuthor()))  # type: ignore

        assert Activity.select().count() == 2


def at(hour, minute=0):
    return datetime.datetime(2026, 11, 4, hour, minute, tzinfo=UTC)


class TestTwoGamesAtOnce:
    """
    Game A: 1h reported at 20:00, 2.5h reported at 21:30 -> 19:00-21:30
    Game B: 1h reported at 20:30, 30m reported at 21:00 -> 19:30-21:00
    """

    def assert_merged(self, user, game_a, game_b):
        a = Activity.select().where(Activity.user == user, Activity.game == game_a)
        b = Activity.select().where(Activity.user == user, Activity.game == game_b)
        assert len(a) == 1
        assert len(b) == 1
        assert (a[0].get_started(), a[0].get_ended()) == (at(19), at(21, 30))
        assert (b[0].get_started(), b[0].get_ended()) == (at(19, 30), at(21))

    def test_when_reported(self, make_user, make_game, make_platform):
        user, _ = make_user()
        game_a = make_game("A")
        game_b = make_game("B")
        pc = make_platform("pc")

        # in the order they would be reported
        for game, seconds, ended in [
            (game_a, 3600, at(20)),
            (game_b, 3600, at(20, 30)),
            (game_b, 1800, at(21)),
            (game_a, 9000, at(21, 30)),
        ]:
            _, err = add_session(
                user=user, game=game, seconds=seconds, platform=pc, timestamp=ended
            )
            assert err is None

        self.assert_merged(user, game_a, game_b)

    def test_retroactively(self, make_user, make_game, make_platform):
        user, _ = make_user()
        game_a = make_game("A")
        game_b = make_game("B")
        pc = make_platform("pc")
        for game, seconds, ended in [
            (game_a, 3600, at(20)),
            (game_a, 9000, at(21, 30)),
            (game_b, 3600, at(20, 30)),
            (game_b, 1800, at(21)),
        ]:
            Activity.create(
                user=user, game=game, platform=pc, seconds=seconds, timestamp=ended
            )

        for group in find_overlapping_groups():
            merge_overlapping_group(group)

        self.assert_merged(user, game_a, game_b)
