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
    History,
    LiveActivity,
    db,
)
from tpbackend.game.select import GameSelect
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


def merge_into(
    keep: Activity,
    others: list[Activity],
    started: datetime.datetime,
    ended: datetime.datetime,
):
    """
    Makes `keep` span from `started` to `ended`. `others` are merged into it: their
    history is moved over (so things like where they came from aren't lost), then they're deleted
    """
    with db.atomic():
        for activity in others:
            keep.add_history(
                f"overlapped activity id {activity.get_id()} ({activity.get_seconds()} seconds @ {activity.get_datetime().isoformat()})"
            )
            History.update(activity=keep).where(History.activity == activity).execute()  # type: ignore
            activity.delete_instance()
        if ended != keep.get_ended():
            keep.set_datetime(ended)
        seconds = int((ended - started).total_seconds())
        if seconds != keep.get_seconds():
            keep.set_seconds(seconds)
        keep.save()


def add_session(
    user: User,
    game: Game,
    seconds: int,
    platform: Platform,
    timestamp: datetime.datetime | None = None,
) -> tuple[Activity | None, Exception | None]:
    """
    Adds a new session to the database. If it overlaps existing activities, the longest
    of those is extended to cover all of them instead, and the others are merged into it.
    Returns a tuple of (Activity, None) on success, or (None, Exception) on failure.
    """
    if seconds < MINIMUM_SESSION_LENGTH:
        return None, ValueError(
            f"Session must be at least {MINIMUM_SESSION_LENGTH} seconds long"
        )

    try:
        if platform.get_abbreviation() == "pc":
            platform, created = Platform.get_or_create(
                abbreviation=user.get_pc_platform()
            )

        platform = Platform_or_none(platform.id)  # type: ignore
        if not platform:
            raise Exception("Platform is None somehow... this shouldnt be possible")

        # now if not provided
        timestamp = timestamp or utils2.now()

        started = timestamp - datetime.timedelta(seconds=seconds)
        overlapping_activities = get_overlapping_activities(
            user=user,
            game=game,
            platform=platform,
            incoming_ended_dt=timestamp,
            incoming_seconds=seconds,
        )
        if overlapping_activities:
            # extend the longest overlapping activity to cover all of them and this session
            keep = max(overlapping_activities, key=lambda a: a.get_seconds())
            others = [a for a in overlapping_activities if a.get_id() != keep.get_id()]
            keep.add_history(
                f"Merged in an overlapping session ({seconds} seconds @ {timestamp.isoformat()})"
            )
            merge_into(
                keep,
                others,
                started=min(
                    [started] + [a.get_started() for a in overlapping_activities]
                ),
                ended=max(
                    [timestamp] + [a.get_ended() for a in overlapping_activities]
                ),
            )
            logger.info(
                "Merged session (%s seconds @ %s) and %s other activities into activity id %s",
                seconds,
                timestamp.isoformat(),
                len(others),
                keep.get_id(),
            )
            return keep, None

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


def adopt_name(game: Game, external_name: str, source: str) -> tuple[str, bool]:
    """
    For matching our games with IGDB games:
    if the names differ, take the external name and keep ours as alias.
    returns (report, conflict), conflict means another game already has that name so we didn't rename
    """
    if external_name == game.get_name():
        return "", False

    out = "⚠️ Name mismatch!"
    out += f"\n- Our name: `{game.get_name()}`"
    out += f"\n- {source} name: `{external_name}`"

    # an alias of this game is fine, eg going back to an earlier IGDB ID
    if external_name not in game.get_aliases():
        other = GameSelect.by_name_or_alias(external_name)
        if other and other.get_id() != game.get_id():
            out += f"\n OTHER GAME HAS {source} NAME AS NAME OR ALIAS: '{other.get_label()}' (id: {other.get_id()})"
            return out, True

    old_name = game.get_name()
    game.remove_alias(external_name)
    game.set_name(external_name)
    game.add_alias(old_name)
    out += f"\n- Replaced name with {source} name and added old name as alias\n"
    return out, False


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
            ("release_year", target.set_release_year),
            # merging shouldn't uncensor anything
            ("nsfw", target.set_nsfw),
        ]:
            if getattr(source, field) and not getattr(target, field):
                setter(getattr(source, field))

        # an uploaded cover is kept, unless target has its own
        uploaded = source.get_uploaded_cover()
        if uploaded and not target.get_uploaded_cover():
            target.set_uploaded_cover(uploaded)

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


def sync_activities_hidden(game: Game) -> int:
    """
    Sets hidden state of all of games activities to match the game.
    Returns how many activities were changed.
    """
    changed = 0
    for activity in Activity.select().where(Activity.game == game):
        activity = cast(Activity, activity)
        if activity.get_hidden() == game.get_hidden():
            continue
        activity.set_hidden(game.get_hidden())
        activity.save()
        changed += 1
    return changed


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
    merge_into(
        keep,
        [a for a in group if a.get_id() != keep.get_id()],
        started=min(a.get_started() for a in group),
        ended=max(a.get_ended() for a in group),
    )

    logger.info(
        "Merged %s overlapping activities into activity id %s",
        len(group) - 1,
        keep.get_id(),
    )
    return keep
