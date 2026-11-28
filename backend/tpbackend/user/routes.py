from tpbackend.activity.query import ActivityQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.user.query import UserStatsQuery, UserQuery
from tpbackend.user.models import (
    API_AuthenticatedUser,
    API_PutSettings,
    API_UserWithStats,
    API_User,
)
from tpbackend.api.responses import bad_request, forbidden, not_found
from tpbackend.files.colors import parse_color
from tpbackend.api.auth import AuthenticatedUser, OptionalUser
from tpbackend.permissions import Permission
from tpbackend.storage import Platform, User, db
import logging
from fastapi import APIRouter, Path
from tpbackend.api.params import (
    path_csv,
    query_ts,
    AscDescOrder,
    path_id,
    query_id,
    query_csv,
    query_search,
    query_game_include_children,
    query_platform_include_children,
    sorts,
    offset,
    limit,
)

logger = logging.getLogger("users-routes")
router = APIRouter()


def __get_users_stats(
    # only matters for users asked for by id, private users see themselves
    viewer: User | None,
    uids: list[int] | None = None,
    before: int | None = None,
    after: int | None = None,
    game_id: int | None = None,
    include_children=False,
    platform_id: int | None = None,
    include_child_platforms=False,
    sort="id",
    order="asc",
    offset=None,
    limit=None,
    search="",
) -> list[API_UserWithStats]:
    bf = parseTS(before)
    af = parseTS(after)

    query = UserStatsQuery.base()
    if uids and len(uids) > 0:
        if len(uids) > 100:
            return bad_request("Cannot request more than 100 users at once")
        query = UserStatsQuery.apply_ids(query, uids)
        # private users only see themselves on their own page
        query = UserQuery.not_private(query, viewer)
    else:
        query = UserQuery.not_private(query)

    if bf:
        query = ActivityQuery.before(query, bf)

    if af:
        query = ActivityQuery.after(query, af)

    if game_id:
        query = ActivityQuery.game(query, game_id, include_children)

    if platform_id:
        query = ActivityQuery.platform(query, platform_id, include_child_platforms)

    if search:
        query = UserQuery.public_search(query, search=search)

    query = UserStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, offset))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    return [API_UserWithStats.from_user(user) for user in query]


@router.get(
    "/user-stats/{user_id}",
    tags=["users", "stats"],
    response_model=API_UserWithStats,
)
def get_single_user_stats(
    viewer: OptionalUser,
    user_id: int,
    before=query_ts("before"),
    after=query_ts("after"),
    game: int | None = None,
    include_children: bool = query_game_include_children(),
    platform: int | None = None,
    include_child_platforms: bool = query_platform_include_children(),
) -> API_UserWithStats:
    x = __get_users_stats(
        viewer,
        uids=[int(user_id)],
        before=before,
        after=after,
        game_id=game,
        include_children=include_children,
        platform_id=platform,
        include_child_platforms=include_child_platforms,
    )
    if len(x) == 0:
        return not_found("User not found")
    return x[0]


@router.get(
    "/users-stats/{user_ids}",
    response_model=list[API_UserWithStats],
    tags=["users", "stats"],
)
def get_many_users_stats(
    viewer: OptionalUser,
    user_ids=path_csv("user ids"),
    before=query_ts("before"),
    after=query_ts("after"),
    game=query_id("game"),
    include_children: bool = query_game_include_children(),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
    sort=sorts(list(UserStatsQuery.SORTS.keys()), "id"),
    order: AscDescOrder = "asc",
) -> list[API_UserWithStats]:
    uids = parse_csv(user_ids)
    return __get_users_stats(
        viewer,
        uids=uids,
        before=before,
        after=after,
        game_id=game,
        include_children=include_children,
        platform_id=platform,
        include_child_platforms=include_child_platforms,
        sort=sort,
        order=order,
    )


@router.get(
    "/users-stats",
    tags=["users", "stats"],
    response_model=list[API_UserWithStats],
)
def get_users_stats(
    offset=offset(),
    limit=limit(),
    game=query_id("game"),
    include_children: bool = query_game_include_children(),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
    before=query_ts("before"),
    after=query_ts("after"),
    sort=sorts(list(UserStatsQuery.SORTS.keys()), "playtime"),
    order: AscDescOrder = "desc",
    search=query_search("users"),
) -> list[API_UserWithStats]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_users_stats(
        None,
        before=before,
        after=after,
        game_id=game,
        include_children=include_children,
        platform_id=platform,
        include_child_platforms=include_child_platforms,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
        search=search,
    )


################################################
############# plain user (no stats) ############
################################################


def __get_users(
    # only matters for users asked for by id, private users see themselves
    viewer: User | None,
    ids: list[int] | None = None,
    sort="id",
    order="asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
) -> list[API_User]:
    query = UserQuery.base()
    if search:
        query = UserQuery.public_search(query, search=search)
    if ids and len(ids) > 0:
        query = UserQuery.apply_ids(query=query, user_ids=ids)
        # private users only see themselves on their own page
        query = UserQuery.not_private(query, viewer)
    else:
        query = UserQuery.not_private(query)
    query = UserQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, int(offset)))
    if limit:
        query = query.limit(clamp(limit, 1, 100))
    return [API_User.from_user(u) for u in query]


@router.get(
    "/user/{user_id}",
    tags=["users"],
    response_model=API_User,
)
def get_single_user(viewer: OptionalUser, user_id: int) -> API_User:
    x = __get_users(viewer, ids=[int(user_id)])
    if len(x) == 0:
        return not_found("User not found")
    return x[0]


@router.get(
    "/users/{user_ids}",
    tags=["users"],
    response_model=list[API_User],
)
def get_many_users(
    viewer: OptionalUser,
    user_ids=path_csv("user ids"),
    sort=sorts(list(UserQuery.SORTS.keys()), "id"),
    order: AscDescOrder = "asc",
) -> list[API_User]:
    gids = parse_csv(user_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 users at once")
    return __get_users(
        viewer,
        ids=gids,
        sort=sort,
        order=order,
    )


@router.get(
    "/users",
    tags=["users"],
    response_model=list[API_User],
)
def get_users(
    offset=offset(),
    limit=limit(),
    sort=sorts(list(UserQuery.SORTS.keys()), "id"),
    order: AscDescOrder = "asc",
    search=query_search("users"),
) -> list[API_User]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_users(
        None, sort=sort, order=order, offset=offset, limit=limit, search=search
    )


@router.get(
    "/who_am_i",
    tags=["users", "authenticated"],
    response_model=API_AuthenticatedUser,
)
def who_am_i(user: AuthenticatedUser) -> API_AuthenticatedUser:
    return API_AuthenticatedUser.from_user(user)


# only for our own frontend's settings page, not part of the public API
@router.put(
    "/settings",
    response_model=API_AuthenticatedUser,
    include_in_schema=False,
)
def update_settings(
    user: AuthenticatedUser, data: API_PutSettings
) -> API_AuthenticatedUser:
    # check everything first, so a bad request changes nothing
    if data.move_pc_activity:
        if not user.has_permission(Permission.MANUAL_ACTIVITY):
            return forbidden("You cannot change the platform of your activity")
        # what the user's pc_platform will be after this request
        new_pc_platform = user.get_pc_platform()
        if data.pc_platform is not None:
            new_pc_platform = data.pc_platform
        if new_pc_platform == "pc":
            return bad_request("Pick an operating system to move the activity to")
    try:
        color_primary = parse_color(data.color_primary)
        color_secondary = parse_color(data.color_secondary)
    except ValueError as e:
        return bad_request(f"Color {e}")

    if data.pc_platform is not None and data.pc_platform != user.get_pc_platform():
        user.set_pc_platform(data.pc_platform)

    if data.move_pc_activity:
        move_pc_activity(user)

    # None leaves the color as it is, empty removes it
    if data.color_primary is not None:
        user.set_color_primary(color_primary)
    if data.color_secondary is not None:
        user.set_color_secondary(color_secondary)

    # force_anonymous is up to admins, so it stays when the user turns anonymous off
    for permission, value in [
        (Permission.SHOW_NSFW, data.show_nsfw),
        (Permission.ANONYMOUS, data.anonymous),
        (Permission.HIDE_PLAYING, data.hide_playing),
        (Permission.PRIVATE, data.private),
    ]:
        if value is True:
            user.add_permission(permission)
        elif value is False:
            user.remove_permission(permission)

    user.save()
    return API_AuthenticatedUser.from_user(user)


def move_pc_activity(user: User):
    """moves the user's activity on 'pc' (unknown OS) to their pc_platform, hidden activity too"""
    pc = Platform.get_or_none(Platform.abbreviation == "pc")
    if not pc:
        return
    target, _ = Platform.get_or_create(abbreviation=user.get_pc_platform())
    query = ActivityQuery.base(include_hidden=True)
    query = ActivityQuery.user(query, user)
    query = ActivityQuery.platform(query, pc)
    with db.atomic():
        moved = 0
        # users can't see hidden activity, so the settings page only counts the others
        hidden = 0
        for activity in query:
            activity.set_platform(target)
            activity.save()
            moved += 1
            if activity.get_hidden():
                hidden += 1
        user.add_history(
            f"Moved {moved} activities ({hidden} hidden) from 'pc' to '{target.get_abbreviation()}'"
        )
    logger.info(
        "Moved %s activities of user %s from pc to %s",
        moved,
        user.get_id(),
        target.get_abbreviation(),
    )
