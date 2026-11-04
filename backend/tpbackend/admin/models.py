from peewee import JOIN, fn
from pydantic import BaseModel

from tpbackend.activity.models import API_Activity
from tpbackend.game.models import API_Game
from tpbackend.platform.models import API_Platform
from tpbackend.storage import Activity, DiscordHistory, Game, Platform, User
from tpbackend.user.models import API_AuthenticatedUser
from tpbackend.utils2 import dt_to_ts


def activity_count(**where) -> int:
    """all activities (hidden too) matching eg game=game"""
    query = Activity.select()
    for field, value in where.items():
        query = query.where(getattr(Activity, field) == value)
    return query.count()


def last_activity(**where) -> int | None:
    """newest activity (hidden too) matching eg game=game"""
    query = Activity.select(fn.MAX(Activity.timestamp))
    for field, value in where.items():
        query = query.where(getattr(Activity, field) == value)
    newest = query.scalar()
    if not newest:
        return None
    return dt_to_ts(newest)


def by_last_activity(query, model, activity_field):
    """most recently played first, never played last (newest first)"""
    return (
        query.join(Activity, JOIN.LEFT_OUTER, on=(activity_field == model.id))
        .group_by(model.id)
        .order_by(fn.MAX(Activity.timestamp).desc(nulls="LAST"), model.id.desc())
    )


class Admin_User(API_AuthenticatedUser):
    activity_count: int

    @classmethod
    def from_user(cls, user: User):
        # admins see the real name, even if it's hidden on the site
        return cls(
            **API_AuthenticatedUser.from_user(user).model_dump()
            | {"name": user.get_name(), "display_name": user.get_display_name()},
            activity_count=activity_count(user=user),
        )


class Admin_UserDetails(Admin_User):
    history: list[str]

    @classmethod
    def from_user(cls, user: User):
        return cls(
            **Admin_User.from_user(user).model_dump(),
            history=user.get_history(),
        )


class Admin_DiscordHistory(BaseModel):
    id: int
    timestamp: int
    event: str
    message: str

    @classmethod
    def from_discord_history(cls, entry: DiscordHistory):
        return cls(
            id=entry.get_id(),
            timestamp=dt_to_ts(entry.timestamp),  # type: ignore
            event=entry.event,  # type: ignore
            message=entry.message,  # type: ignore
        )


class Admin_Activity(API_Activity):
    hidden: bool

    @classmethod
    def from_activity(cls, activity: Activity):
        return cls(
            **API_Activity.from_activity(activity).model_dump(),
            hidden=activity.get_hidden(),
        )


class Admin_ActivityDetails(Admin_Activity):
    history: list[str]

    @classmethod
    def from_activity(cls, activity: Activity):
        return cls(
            **Admin_Activity.from_activity(activity).model_dump(),
            history=activity.get_history(),
        )


class Admin_Game(API_Game):
    hidden: bool
    activity_count: int
    last_activity: int | None

    @classmethod
    def from_game(cls, game: Game):
        return cls(
            **API_Game.from_game(game).model_dump(),
            # own hidden, not inherited from parent, that's what can be toggled
            hidden=bool(game.hidden),
            activity_count=activity_count(game=game),
            last_activity=last_activity(game=game),
        )


class Admin_GameDetails(Admin_Game):
    history: list[str]

    @classmethod
    def from_game(cls, game: Game):
        return cls(
            **Admin_Game.from_game(game).model_dump(),
            history=game.get_history(),
        )


class Admin_Platform(API_Platform):
    activity_count: int
    last_activity: int | None
    history: list[str]

    @classmethod
    def from_platform(cls, platform: Platform):
        return cls(
            **API_Platform.from_platform(platform).model_dump(),
            activity_count=activity_count(platform=platform),
            last_activity=last_activity(platform=platform),
            history=platform.get_history(),
        )


class Admin_Permission(BaseModel):
    name: str
    description: str


class Admin_PostUser(BaseModel):
    name: str
    display_name: str | None = None


class Admin_Token(BaseModel):
    token: str


class Admin_TokenInfo(BaseModel):
    """only the hash of a token is stored, so this is all there is to show"""

    id: int
    created: int
    current: bool  # the token this request was made with


class Admin_SetPermissions(BaseModel):
    permissions: list[str]


class Admin_PatchActivity(BaseModel):
    """only fields that are sent are changed"""

    game_id: int | None = None
    platform_id: int | None = None
    user_id: int | None = None
    seconds: int | None = None
    ended: int | None = None
    hidden: bool | None = None


class Admin_MoveActivities(BaseModel):
    from_game_id: int
    to_game_id: int


class Admin_Moved(BaseModel):
    moved: int


class Admin_OverlapGroup(BaseModel):
    keep_id: int
    remove_ids: list[int]


class Admin_OverlapsMerged(BaseModel):
    groups: int
    removed: int


class Admin_PostGame(BaseModel):
    name: str


class Admin_PatchGame(BaseModel):
    """only fields that are sent are changed, null clears"""

    name: str | None = None
    image_url: str | None = None
    release_year: int | None = None
    parent_id: int | None = None
    steam_id: int | None = None
    hidden: bool | None = None


class Admin_SetIGDB(BaseModel):
    igdb_id: int | None


class Admin_SetSGDB(BaseModel):
    sgdb_id: int | None


class Admin_Alias(BaseModel):
    alias: str


class Admin_MergeGame(BaseModel):
    into_game_id: int


class Admin_MergePreview(BaseModel):
    activity_count: int
    new_aliases: list[str]


class Admin_PostPlatform(BaseModel):
    abbreviation: str


class Admin_PatchPlatform(BaseModel):
    """only fields that are sent are changed, null clears"""

    abbreviation: str | None = None
    name: str | None = None
    color_primary: str | None = None
    color_secondary: str | None = None
    icon: str | None = None
