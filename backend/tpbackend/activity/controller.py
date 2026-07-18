from tpbackend.activity.models import API_Activity, API_PostActivity
from tpbackend.activity.query import ActivityQuery
from tpbackend.api.responses import (
    bad_request,
    forbidden,
    internal_server_error,
    not_found,
)
from tpbackend.game.select import GameSelect
from tpbackend.globals import MINIMUM_SESSION_LENGTH
from tpbackend.operations import add_session
from tpbackend.storage import Activity, Platform_or_none, User
from tpbackend.utils2 import ts_to_dt
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
        if not game:
            return not_found("Game not found")
    elif data.igdb_id:
        game = GameSelect.by_igdb_id(data.igdb_id)
        if not game:
            # TODO create the game!
            return bad_request("not implemented")
    else:
        return bad_request("Game id or igdb id must be provided")

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
