import datetime
import logging
from typing import cast

from tpbackend import utils2
from tpbackend.api_v2.games.select import GameSelect
from tpbackend.storage.storage_v2 import (
    Activity_or_none,
    Platform_or_none,
    User,
    Game,
    Platform,
    Activity,
)
from tpbackend.globals import MINIMUM_SESSION_LENGTH

logger = logging.getLogger("operations")


def get_overlapping_activity(
    user: User,
    game: Game,
    platform: Platform,
    incoming_ended_dt: datetime.datetime,
    incoming_seconds: int,
) -> Activity | None:
    """
    Returns None if no overlap.
    Returns old activity if overlap is detected (it should be removed)
    """
    # get last activity for this user/game/platform
    last_activity = (
        Activity.select()
        .where(
            (Activity.user == user)
            & (Activity.game == game)
            & (Activity.platform == platform)
        )
        .order_by(Activity.timestamp.desc())
        .first()
    )
    if not last_activity:
        return None

    last_activity = cast(Activity, last_activity)
    last_ended_ts = last_activity.get_timestamp()
    new_ended_ts = int(incoming_ended_dt.timestamp() * 1000)
    # calculate time between the activities
    delta_ms = new_ended_ts - last_ended_ts
    delta_s = delta_ms / 1000
    if delta_s < incoming_seconds:
        # if the last_activity ended when you were still playing (according to this new incoming activity), it's an overlap
        logger.info("⚠️ Detected overlapping activity: %s", last_activity)
        return last_activity
    return None


def add_session(
    user: User,
    game: Game,
    seconds: int,
    platform: Platform | None = None,
    timestamp: datetime.datetime | None = None,
) -> tuple[Activity | None, Exception | None]:
    """
    Adds a new session to the database.
    Returns a tuple of (Activity, None) on success, or (None, Exception) on failure.
    """
    if seconds < MINIMUM_SESSION_LENGTH:
        return None, ValueError(
            f"Session must be at least {MINIMUM_SESSION_LENGTH} seconds long"
        )

    try:
        # use default platform if not provided
        platform = platform or user.get_default_platform()
        if platform.get_abbreviation() == "pc":
            platform, created = Platform.get_or_create(
                abbreviation=user.get_pc_platform()
            )

        platform = Platform_or_none(platform.id)  # type: ignore
        if not platform:
            raise Exception("Platform is None somehow... this shouldnt be possible")

        # now if not provided
        timestamp = timestamp or utils2.now()

        # Check for overlapping activity
        overlapping_activity = get_overlapping_activity(
            user=user,
            game=game,
            platform=platform,
            incoming_ended_dt=timestamp,
            incoming_seconds=seconds,
        )
        if overlapping_activity is not None:
            logger.info(
                "Deleting overlapping activity %s for user %s",
                overlapping_activity,
                user,
            )
            overlapping_activity.delete_instance()  # or maybe just hide...

        raw_activity = Activity.create(
            user=user,
            game=game,
            seconds=seconds,
            platform=platform,
            timestamp=timestamp,
            hidden=game.get_hidden(),
        )

        activity = Activity_or_none(raw_activity.id, include_hidden=True)
        if not activity:
            raise Exception("Failed to retrieve newly created activity")

        logger.info(
            "Added activity id %s for user %s: %s (%s) - %s seconds @ %s (hidden: %s)",
            activity.get_id(),
            activity.get_user().get_name(),
            activity.get_game().get_name(),
            activity.get_platform().get_abbreviation(),
            activity.get_seconds(),
            activity.get_datetime().isoformat(),
            activity.get_hidden(),
        )

        return activity, None
    except Exception as e:
        logger.error("Failed to add session for user %s: %s", user.id, e)
        return None, e


def remove_game_images(game: Game) -> str:
    Game.update(small_image=None, large_image=None).where(Game.id == game.id).execute()  # type: ignore
    logger.info("Removed images for game %s", game.name)
    return f"Images for game '{game.name}' removed successfully."


def remove_session(user: User, sessionId: int):
    activity = Activity_or_none(sessionId, include_hidden=True)
    if not activity:
        return f"ERROR: Session {sessionId} not found"
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.delete_instance()
    return f"Session {sessionId} removed successfully."


def merge_games(user: User, gameId1: int, gameId2: int):
    game1 = GameSelect.by_id(gameId1)
    if not game1:
        return f"ERROR: Game with ID {gameId1} not found"
    game2 = GameSelect.by_id(gameId2)
    if not game2:
        return f"ERROR: Game with ID {gameId2} not found"
    Activity.update(game=game2).where(
        (Activity.game == game1) & (Activity.user == user)
    ).execute()
    return f"Game '{game1.name}' merged into '{game2.name}' successfully for your user"


def set_default_platform(user: User, platform: str) -> str:
    user.default_platform = platform  # type: ignore
    user.save()
    return f"Your default platform is now **{user.default_platform}**"


def set_platform_for_session(user: User, sessionId: int, platform: Platform) -> bool:
    activity = Activity_or_none(sessionId)
    if not activity:
        return False
    if activity.user.id != user.id:
        return False
    if activity.platform == platform:
        return False
    activity.set_platform(platform)
    activity.save()
    return True


def modify_session_date(user: User, sessionId: int, new_date: datetime.datetime) -> str:
    activity = Activity_or_none(sessionId)
    if not activity:
        return f"ERROR: Session {sessionId} not found"
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.set_datetime(new_date)
    activity.save()
    return f"Session {sessionId} date has been modified to {new_date.strftime('%Y-%m-%d %H:%M:%S')} UTC"
