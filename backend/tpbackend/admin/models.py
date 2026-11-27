from peewee import JOIN, fn
from pydantic import BaseModel, Field

from tpbackend.activity.models import API_Activity
from tpbackend.game.models import API_Game
from tpbackend.platform.models import API_Platform
from tpbackend.storage import (
    Activity,
    DiscordHistory,
    DiscordPresence,
    Game,
    History,
    HistoryMixin,
    LiveActivity,
    Platform,
    User,
)
from tpbackend.permissions import Permission
from tpbackend.user.models import API_AuthenticatedUser
from tpbackend.utils2 import dt_to_ts, dt_to_ts_or_none


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


class Admin_History(BaseModel):
    timestamp: int
    actor_id: int | None = Field(description="Who made the change, null if nobody did")
    actor_name: str | None
    message: str

    @classmethod
    def from_history(cls, entry: History):
        actor_id = None
        actor_name = None
        actor = entry.get_actor()
        if actor:
            actor_id = actor.get_id()
            # admins see the real name, even if it's hidden on the site
            actor_name = actor.get_name()
        return cls(
            timestamp=dt_to_ts(entry.timestamp),  # type: ignore
            actor_id=actor_id,
            actor_name=actor_name,
            message=entry.message,  # type: ignore
        )


def history_of(model: HistoryMixin) -> list[Admin_History]:
    return [Admin_History.from_history(h) for h in model.get_history_entries()]


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
    history: list[Admin_History]

    @classmethod
    def from_user(cls, user: User):
        return cls(
            **Admin_User.from_user(user).model_dump(),
            history=history_of(user),
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
    history: list[Admin_History]

    @classmethod
    def from_activity(cls, activity: Activity):
        return cls(
            **Admin_Activity.from_activity(activity).model_dump(),
            history=history_of(activity),
        )


def uploaded_cover_id(game: Game) -> str | None:
    image = game.get_uploaded_cover()
    if image:
        return image.get_id()
    return None


class Admin_Game(API_Game):
    hidden: bool
    own_nsfw: bool = Field(description="Set on this game, not inherited from a parent")
    activity_count: int
    last_activity: int | None
    uploaded_cover: str | None = Field(description="ImageFile id of the uploaded cover")

    @classmethod
    def from_game(cls, game: Game):
        return cls(
            **API_Game.from_game(game).model_dump(),
            uploaded_cover=uploaded_cover_id(game),
            # own hidden, not inherited from parent, that's what can be toggled
            hidden=bool(game.hidden),
            own_nsfw=bool(game.nsfw),
            activity_count=activity_count(game=game),
            last_activity=last_activity(game=game),
        )


class Admin_GameDetails(Admin_Game):
    history: list[Admin_History]

    @classmethod
    def from_game(cls, game: Game):
        return cls(
            **Admin_Game.from_game(game).model_dump(),
            history=history_of(game),
        )


class Admin_Platform(API_Platform):
    activity_count: int
    last_activity: int | None
    history: list[Admin_History]

    @classmethod
    def from_platform(cls, platform: Platform):
        return cls(
            **API_Platform.from_platform(platform).model_dump(),
            activity_count=activity_count(platform=platform),
            last_activity=last_activity(platform=platform),
            history=history_of(platform),
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


class Admin_SetDiscordId(BaseModel):
    """null or empty removes it"""

    discord_id: str | None


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
    cover_disabled: bool | None = None
    nsfw: bool | None = None
    release_year: int | None = None
    parent_id: int | None = None
    steam_id: int | None = None
    hidden: bool | None = None


class Admin_CoverUrl(BaseModel):
    url: str


class Admin_SetIGDB(BaseModel):
    igdb_id: int | None


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
    parent_id: int | None = None


class Admin_DiscordActivity(BaseModel):
    """an activity in someone's Discord presence, as Discord gives it"""

    type: str = Field(
        description="playing, streaming, listening, watching or competing"
    )
    name: str | None
    details: str | None
    state: str | None
    platform: str | None
    start: int | None = Field(description="When Discord says it started")

    @classmethod
    def from_activity(cls, activity):
        return cls(
            type=activity.type.name,
            name=activity.name,
            details=getattr(activity, "details", None),
            state=getattr(activity, "state", None),
            platform=getattr(activity, "platform", None),
            start=dt_to_ts_or_none(getattr(activity, "start", None)),
        )


class Admin_TrackedPresence(BaseModel):
    """a session the presence tracker is tracking, see DiscordPresence"""

    game_name: str
    platform: str
    started: int = Field(description="When the bot first saw them playing it")
    discord_started: int | None = Field(
        description="The earliest start Discord reported"
    )
    last_seen: int

    @classmethod
    def from_presence(cls, presence: DiscordPresence):
        return cls(
            game_name=presence.get_game_name(),
            platform=presence.get_platform(),
            started=dt_to_ts(presence.get_started()),
            discord_started=dt_to_ts_or_none(presence.get_discord_started()),
            last_seen=dt_to_ts(presence.get_last_seen()),
        )


class Admin_PresenceMember(BaseModel):
    discord_user_id: str
    discord_user_name: str
    user_id: int | None = Field(
        description="Null if they have no user yet, it's created when a session is stored"
    )
    synced: bool = Field(
        description="Their sessions are stored: the user has oblivionis_sync, or gets it when created"
    )
    tracked: list[Admin_TrackedPresence] = Field(
        description="A session for each game they're playing, oldest first"
    )
    activities: list[Admin_DiscordActivity] = Field(
        description="Empty if the bot doesn't see them in any server"
    )


class Admin_Presence(BaseModel):
    connected: bool = Field(description="The bot is logged in to Discord")
    last_checked: int | None = Field(
        description="When everyone's presence was last checked, null if not since the backend started"
    )
    members: list[Admin_PresenceMember] = Field(
        description="Everyone who is playing something or has a tracked session"
    )


class Admin_LiveActivity(BaseModel):
    """a manual tracking session that's running"""

    id: int
    user_id: int
    user_name: str
    game_id: int
    game_name: str
    platform_id: int
    platform_abbreviation: str
    started: int
    manual_activity: bool = Field(
        description="The user has manual_activity, without it they can't stop it"
    )

    @classmethod
    def from_live_activity(cls, live: LiveActivity):
        user = live.get_user()
        game = live.get_game()
        platform = live.get_platform()
        return cls(
            id=live.get_id(),
            user_id=user.get_id(),
            # admins see the real name, even if it's hidden on the site
            user_name=user.get_name(),
            game_id=game.get_id(),
            game_name=game.get_name(),
            platform_id=platform.get_id(),
            platform_abbreviation=platform.get_abbreviation(),
            started=live.get_started_timestamp(),
            manual_activity=user.has_permission(Permission.MANUAL_ACTIVITY),
        )
