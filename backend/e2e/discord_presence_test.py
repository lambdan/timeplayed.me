import datetime

from tpbackend.discord import presence
from tpbackend.discord.presence import Playing
from tpbackend.storage import Activity, DiscordPresence, User

T0 = datetime.datetime(2026, 11, 22, 12, 0, tzinfo=datetime.UTC)


def minutes(n: float) -> datetime.timedelta:
    return datetime.timedelta(minutes=n)


def update(playing: Playing | None, now: datetime.datetime):
    presence.update("1234", "discordguy", playing, now)


def play(playing: Playing, start: float, end: float):
    """
    Seen playing from minute `start` to `end`, checked every minute like the check loop
    """
    for m in range(int(start), int(end) + 1):
        update(playing, T0 + minutes(m))


def activities() -> list[Activity]:
    return list(Activity.select().order_by(Activity.timestamp))


class TestDiscordPresence:
    def test_start_check_in_and_stop(self):
        play(Playing("Some Game", "ps5", T0), 1, 3)

        # still playing, nothing stored yet
        assert Activity.select().count() == 0
        stored = DiscordPresence.get()
        # first seen a minute after Discord says they started
        assert stored.get_started() == T0 + minutes(1)
        assert stored.get_discord_started() == T0
        assert stored.get_last_seen() == T0 + minutes(3)

        update(None, T0 + minutes(4))

        assert DiscordPresence.select().count() == 0
        [activity] = activities()
        assert activity.get_game().get_name() == "Some Game"
        assert activity.get_platform().get_abbreviation() == "ps5"
        assert activity.get_user() == User.get(User.discord_id == "1234")
        # Discord's start is earlier than ours, so it wins
        assert activity.get_started() == T0
        assert activity.get_ended() == T0 + minutes(4)
        assert any(
            "Activity source: Discord presence" in h
            and "first seen: 2026-11-22T12:01:00Z, Discord start: 2026-11-22T12:00:00Z, ended: 2026-11-22T12:04:00Z"
            in h
            for h in activity.get_history()
        )

    def test_switching_games(self):
        play(Playing("First", "ps5", T0), 0, 29)
        update(Playing("Second", "ps5", T0 + minutes(30)), T0 + minutes(30))

        [first] = activities()
        assert first.get_game().get_name() == "First"
        assert first.get_seconds() == 30 * 60
        assert DiscordPresence.get().get_game_name() == "Second"

    def test_same_game_on_another_platform_is_another_session(self):
        play(Playing("Game", "ps5", T0), 0, 29)
        update(Playing("Game", "pc", T0 + minutes(30)), T0 + minutes(30))

        [first] = activities()
        assert first.get_platform().get_abbreviation() == "ps5"
        assert DiscordPresence.get().get_platform() == "pc"

    def test_discord_resetting_its_start_keeps_ours(self):
        play(Playing("Game", "ps5", T0), 0, 29)
        # the game resets Discord's start mid-session
        play(Playing("Game", "ps5", T0 + minutes(30)), 30, 59)

        stored = DiscordPresence.get()
        assert stored.get_started() == T0
        assert stored.get_discord_started() == T0
        update(None, T0 + minutes(60))

        [activity] = activities()
        assert activity.get_started() == T0
        assert activity.get_ended() == T0 + minutes(60)

    def test_discord_start_missing_for_a_while_keeps_it(self):
        play(Playing("Game", "ps5", T0), 0, 9)
        play(Playing("Game", "ps5", None), 10, 19)

        assert DiscordPresence.get().get_discord_started() == T0

    def test_no_start_from_discord_starts_now(self):
        play(Playing("Game", "ps5", None), 0, 19)
        update(None, T0 + minutes(20))

        [activity] = activities()
        assert activity.get_started() == T0
        assert activity.get_seconds() == 20 * 60

    def test_never_seen_again_after_starting_is_not_stored(self):
        update(Playing("Game", "ps5", None), T0)
        # bot is down right after
        update(None, T0 + minutes(300))

        assert Activity.select().count() == 0
        assert DiscordPresence.select().count() == 0

    def test_stopped_while_bot_was_down_ends_at_last_seen(self):
        play(Playing("Game", "ps5", T0), 1, 10)
        # bot is down for hours, then sees they're not playing
        update(None, T0 + minutes(300))

        [activity] = activities()
        assert activity.get_started() == T0
        assert activity.get_ended() == T0 + minutes(10)

    def test_still_playing_after_bot_was_down_is_one_session(self):
        playing = Playing("Game", "ps5", T0)
        play(playing, 1, 10)
        # bot is down for an hour, they're still playing with the same start
        play(playing, 70, 79)
        # the part before the downtime was stored
        assert len(activities()) == 1

        update(None, T0 + minutes(80))

        # and merged into the whole session
        [activity] = activities()
        assert activity.get_started() == T0
        assert activity.get_ended() == T0 + minutes(80)

    def test_blends_with_oblivionis(self):
        # Oblivionis saw the same session and synced it, ending a bit earlier
        from tpbackend.oblivionis import sync

        sync.parseActivity(
            {
                "game_name": "Game",
                "duration": 59 * 60,
                "dt": T0,
                "discord_user_name": "discordguy",
                "discord_user_id": "1234",
                "platform": "ps5",
            },
            ended=T0 + minutes(59),
        )
        play(Playing("Game", "ps5", T0), 1, 59)
        update(None, T0 + minutes(60))

        [activity] = activities()
        assert activity.get_started() == T0
        assert activity.get_ended() == T0 + minutes(60)
        # what both sources said is kept
        history = activity.get_history()
        assert any("Activity source: Oblivionis" in h for h in history)
        assert any("Activity source: Discord presence" in h for h in history)

    def test_playstation_8_hours_is_dropped(self):
        play(Playing("Game", "ps5", T0), 1, 8 * 60 - 1)
        update(None, T0 + minutes(8 * 60))

        assert Activity.select().count() == 0
        user = User.get(User.discord_id == "1234")
        assert any("Dropped Discord presence activity" in h for h in user.get_history())
