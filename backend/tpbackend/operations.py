import datetime
import logging
from typing import cast

from tpbackend import utils2
from .storage import (
    Activity_or_none,
    Platform_or_none,
    User,
    Game,
    Platform,
    Activity,
    LiveActivity,
    db,
)
from tpbackend.globals import MINIMUM_SESSION_LENGTH

logger = logging.getLogger("operations")


def get_overlapping_activities(
    user: User,
    game: Game,
    platform: Platform,
    incoming_ended_dt: datetime.datetime,
    incoming_seconds: int,
) -> list[Activity]:
    """
    Returns all activities for this user/game/platform that overlap the incoming one.
    They should be merged into the incoming activity and removed.
    """
    incoming_started_dt = incoming_ended_dt - datetime.timedelta(
        seconds=incoming_seconds
    )
    # anything that ended when or after the incoming activity started might overlap
    candidates = Activity.select().where(
        (Activity.user == user)
        & (Activity.game == game)
        & (Activity.platform == platform)
        & (Activity.timestamp >= incoming_started_dt)
    )

    overlapping = []
    for activity in candidates:
        activity = cast(Activity, activity)
        if activity.get_started() <= incoming_ended_dt:
            logger.info("⚠️ Detected overlapping activity: %s", activity)
            overlapping.append(activity)
    return overlapping


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

        # Merge all overlapping activities into this one
        overlapping_activities = get_overlapping_activities(
            user=user,
            game=game,
            platform=platform,
            incoming_ended_dt=timestamp,
            incoming_seconds=seconds,
        )
        overlap_msgs = []
        started = timestamp - datetime.timedelta(seconds=seconds)
        for overlapping_activity in overlapping_activities:
            overlap_msg = f"overlapped activity id {overlapping_activity.get_id()} ({overlapping_activity.get_seconds()} seconds @ {overlapping_activity.get_datetime().isoformat()})"
            logger.info(overlap_msg)
            overlap_msgs.append(overlap_msg)
            # the merged activity spans from the earliest start to the latest end
            started = min(started, overlapping_activity.get_started())
            timestamp = max(timestamp, overlapping_activity.get_ended())
            overlapping_activity.delete_instance()  # or maybe just hide...
        seconds = int((timestamp - started).total_seconds())

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

        if overlap_msgs:
            for overlap_msg in overlap_msgs:
                activity.add_history(overlap_msg)
            activity.save()

        return activity, None
    except Exception as e:
        logger.error("Failed to add session for user %s: %s", user.id, e)
        return None, e


def merge_aliases(source: Game, target: Game) -> list[str]:
    """
    Sources name and aliases that target doesn't already have (as name or alias)
    """
    have = {target.get_name(), *target.get_aliases()}
    res = []
    for name in [source.get_name(), *source.get_aliases()]:
        if name not in have and name not in res:
            res.append(name)
    return res


def merge_games(source: Game, target: Game) -> int:
    """
    Merges source into target: moves all activities (all users), live activities and
    child games over, keeps sources name and aliases as aliases, then deletes source.
    Returns how many activities were moved.
    """
    if source.get_id() == target.get_id():
        raise ValueError("Cannot merge a game into itself")

    # all or nothing, a half merged game would be a mess to clean up
    with db.atomic():
        activities = list(Activity.select().where(Activity.game == source))  # type: ignore
        for act in activities:
            act.set_game(target)
            act.save()

        LiveActivity.update(game=target).where(LiveActivity.game == source).execute()  # type: ignore

        for child in source.get_children(recursive=False):
            # target can be a child of source, its parent is cleared when source is deleted
            if child.get_id() != target.get_id():
                child.set_parent(target)
                child.save()

        # keep anything target is missing. steam_id is unique, so clear it from source first
        if source.steam_id and not target.steam_id:
            steam_id = source.steam_id
            source.set_steam_id(None)
            source.save()
            target.set_steam_id(steam_id)  # type: ignore
        # the setters add history, so it's visible what came from the merge
        for field, setter in [
            ("sgdb_id", target.set_sgdb_id),
            ("image_url", target.set_image_url),
            ("release_year", target.set_release_year),
        ]:
            if getattr(source, field) and not getattr(target, field):
                setter(getattr(source, field))

        for alias in merge_aliases(source, target):
            target.add_alias(alias)
        target.add_history(
            f"Merged in '{source.get_name()}' ({source.get_id()}), {len(activities)} activities"
        )
        target.save()

        logger.info(
            "Merged game %s '%s' into %s '%s' (%s activities)",
            source.get_id(),
            source.get_name(),
            target.get_id(),
            target.get_name(),
            len(activities),
        )
        source.delete_instance()
    return len(activities)


def find_overlapping_groups() -> list[list[Activity]]:
    """
    Groups of activities (same user/game/platform) that overlap each other in time.
    Only groups with more than one activity are returned, each sorted by start.
    """
    by_key: dict[tuple[int, int, int], list[Activity]] = {}
    for activity in Activity.select():
        activity = cast(Activity, activity)
        key = (activity.user_id, activity.game_id, activity.platform_id)  # type: ignore
        by_key.setdefault(key, []).append(activity)

    groups = []
    for activities in by_key.values():
        activities.sort(key=lambda a: a.get_started())
        group = [activities[0]]
        group_ended = activities[0].get_ended()
        for activity in activities[1:]:
            if activity.get_started() <= group_ended:
                group.append(activity)
                group_ended = max(group_ended, activity.get_ended())
                continue
            if len(group) > 1:
                groups.append(group)
            group = [activity]
            group_ended = activity.get_ended()
        if len(group) > 1:
            groups.append(group)
    return groups


def merge_overlapping_group(group: list[Activity]) -> Activity:
    """
    Merges overlapping activities into the longest one, which then spans from the
    earliest start to the latest end. The others are deleted.
    """
    keep = max(group, key=lambda a: a.get_seconds())
    started = min(a.get_started() for a in group)
    ended = max(a.get_ended() for a in group)

    with db.atomic():
        for activity in group:
            if activity.get_id() == keep.get_id():
                continue
            keep.add_history(
                f"overlapped activity id {activity.get_id()} ({activity.get_seconds()} seconds @ {activity.get_datetime().isoformat()})"
            )
            activity.delete_instance()
        if ended != keep.get_ended():
            keep.set_datetime(ended)
        seconds = int((ended - started).total_seconds())
        if seconds != keep.get_seconds():
            keep.set_seconds(seconds)
        keep.save()

    logger.info(
        "Merged %s overlapping activities into activity id %s",
        len(group) - 1,
        keep.get_id(),
    )
    return keep
