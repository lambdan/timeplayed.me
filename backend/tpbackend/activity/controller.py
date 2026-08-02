from tpbackend.activity.models import (
    API_Activity,
    API_LiveActivity,
    API_PostActivity,
    API_PostLiveActivity,
)
from tpbackend.activity.query import ActivityQuery
from tpbackend.api.responses import (
    bad_request,
    forbidden,
    internal_server_error,
    not_found,
)
from tpbackend.game.select import GameSelect
from tpbackend.globals import MINIMUM_SESSION_LENGTH
from tpbackend.igdb.controller import get_or_create_game
from tpbackend.operations import add_session
from tpbackend.storage import (
    Activity,
    LiveActivity,
    LiveActivity_or_none,
    Platform_or_none,
    User,
)
from tpbackend.utils2 import now, ts_to_dt
import logging
from typing import cast

logger = logging.getLogger("activity_controller")


def add_through_api(user: User, data: API_PostActivity) -> API_Activity:
    if data.seconds < MINIMUM_SESSION_LENGTH:
        return bad_request(
            f"Activity not long enough (minimum is {MINIMUM_SESSION_LENGTH} seconds)"
        )

    game = None
    if data.game_id:
        game = GameSelect.by_id(data.game_id)
    elif data.igdb_id:
        game = get_or_create_game(
            data.igdb_id, history_create_msg="Created during API activity add"
        )
    else:
        return bad_request("game_id or igdb_id must be provided")

    if not game:
        return not_found("Game not found")

    platform = None
    if data.platform_id:
        platform = Platform_or_none(data.platform_id)
        if not platform:
            return not_found("Platform not found")

    added = add_session(
        user=user,
        game=game,
        seconds=data.seconds,
        platform=platform,
    )
    if added[0]:
        activity = added[0]
        activity.add_history("Activity source: API")
        if data.emulated:
            activity.set_emulated(True)
        activity.save()
        return API_Activity.from_activity(activity)
    logger.error("Failed to add activity for user %s, game %s", user.id, game.id)
    return internal_server_error("Something went wrong...")


def delete_through_api(user: User, activity_id: int):
    act = ActivityQuery.base(include_hidden=True)
    # act = act.user(act, user)
    act = ActivityQuery.id(act, activity_id)
    get = act.first()
    if not get:
        return not_found("Activity not found")
    get = cast(Activity, get)
    if get.get_user() == user:
        get.delete_instance()
        return "Deleted!"
    else:
        return forbidden("You cannot delete someone else's activity")


def get_live_activity_through_api(user: User) -> API_LiveActivity:
    act = LiveActivity_or_none(user=user)
    if not act:
        return not_found("No live activity found")
    return API_LiveActivity.from_live_activity(act)


def abort_live_activity_through_api(user: User):
    act = LiveActivity_or_none(user=user)
    if not act:
        return not_found("No live activity found")
    act.delete_instance()
    return "Aborted"


def stop_live_activity_through_api(user: User) -> API_Activity:
    act = LiveActivity_or_none(user=user)
    if not act:
        return not_found("No live activity found")

    started = act.get_started_datetime()
    duration = now() - started
    seconds = int(duration.total_seconds())

    result = add_session(
        user=user,
        platform=act.get_platform(),
        game=act.get_game(),
        seconds=seconds,
    )

    sesh = result[0]
    act.delete_instance()  # Remove the live session from db
    if sesh:
        sesh.add_history("Activity source: API live activity")
        sesh.save()
        return API_Activity.from_activity(sesh)
    if isinstance(result[1], ValueError):
        return bad_request("Session ended, but not saved because it was too short")
    return internal_server_error("Something went wrong...")


def start_live_activity_through_api(
    user: User, data: API_PostLiveActivity
) -> API_LiveActivity:
    # already has one?
    existing = LiveActivity_or_none(user=user)
    if existing:
        return bad_request("You already have a live activity running")

    if not data.game_id and not data.igdb_id:
        return bad_request("game_id or igdb_id must be provided")

    game = None
    if data.game_id:
        game = GameSelect.by_id(data.game_id)
    elif data.igdb_id:
        game = get_or_create_game(
            data.igdb_id, history_create_msg="Created during API live activity start"
        )
    if not game:
        return not_found("Game not found")

    platform = user.get_default_platform()
    if data.platform_id:
        platform = Platform_or_none(data.platform_id)
        if not platform:
            return not_found("Platform not found")

    new = LiveActivity.create(user=user, game=game, platform=platform, started=now())
    logger.info(
        f"User {user.get_name()} started live activity for game {game.get_name()} on platform {platform.get_name()}"
    )
    return API_LiveActivity.from_live_activity(new)
