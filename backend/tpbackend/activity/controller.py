from tpbackend.activity.models import API_Activity, API_PostActivity
from tpbackend.api.responses import bad_request, internal_server_error, not_found
from tpbackend.game.select import GameSelect
from tpbackend.globals import MINIMUM_SESSION_LENGTH
from tpbackend.operations import add_session
from tpbackend.storage import Platform_or_none, User
from tpbackend.utils2 import ts_to_dt
import logging

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
