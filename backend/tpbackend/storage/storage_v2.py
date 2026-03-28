import asyncio
import os
import logging
from typing import cast
from datetime import datetime, timezone, timedelta

from tpbackend import utils
from tpbackend.permissions import DEFAULT_PERMISSIONS
from tpbackend.storage.reset_sequence import reset_sequences
from tpbackend.api_models import (
    PublicGameModel,
    PublicPlatformModel,
    PublicUserModel,
    PublicActivityModel,
)

logger = logging.getLogger("storage_v2")

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
    AutoField,
)
from playhouse.postgres_ext import PostgresqlExtDatabase, ArrayField

db = PostgresqlExtDatabase(
    os.environ.get("DB_NAME_TIMEPLAYED"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
)


class BaseModel(Model):
    class Meta:
        database = db


class Platform(BaseModel):
    """
    Platform (V2)
    """

    id = AutoField()
    abbreviation = CharField(unique=True)
    name = CharField(null=True)
    color_primary = CharField(null=True, column_name="color_primary")
    color_secondary = CharField(null=True, column_name="color_secondary")
    icon = CharField(null=True)

    def get_id(self) -> int:
        return cast(int, self.id)

    def get_abbreviation(self) -> str:
        return cast(str, self.abbreviation)

    def get_name(self) -> str | None:
        return cast(str | None, self.name)

    def get_display_name(self) -> str:
        return (self.get_name() or self.get_abbreviation()).strip()

    def get_color_primary(self) -> str | None:
        return cast(str | None, self.color_primary)

    def get_color_secondary(self) -> str | None:
        return cast(str | None, self.color_secondary)

    def get_icon(self) -> str | None:
        return cast(str | None, self.icon)

    def get_api_model(self) -> PublicPlatformModel:
        return PublicPlatformModel(
            id=self.get_id(),
            abbreviation=self.get_abbreviation(),
            name=self.get_name(),
            color_primary=self.get_color_primary(),
            color_secondary=self.get_color_secondary(),
            icon=self.get_icon(),
        )


class User(BaseModel):
    """
    User (V2)
    """

    id = AutoField()
    discord_id = CharField(unique=True, null=True)
    name = CharField()
    default_platform = ForeignKeyField(
        Platform, default=lambda: Platform.get_or_create(abbreviation="win")[0]
    )
    pc_platform = CharField(default="win")
    permissions = ArrayField(TextField, default=lambda: DEFAULT_PERMISSIONS)  # type: ignore

    def get_id(self) -> int:
        return cast(int, self.id)

    def get_discord_id(self) -> str | None:
        return cast(str | None, self.discord_id)

    def get_name(self) -> str:
        return cast(str, self.name)

    def get_default_platform(self) -> Platform:
        return cast(Platform, self.default_platform)

    def get_pc_platform(self) -> str:
        return cast(str, self.pc_platform)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def add_permission(self, permission: str) -> bool:
        """
        Returns true if permission was added, false if user already had permission.
        """
        if not self.has_permission(permission):
            self.permissions.append(permission)  # type: ignore
            self.save()
            return True
        return False

    def remove_permission(self, permission: str) -> bool:
        """
        Returns true if permission was removed, false if user didn't have permission.
        """
        if self.has_permission(permission):
            self.permissions.remove(permission)  # type: ignore
            self.save()
            return True
        return False

    def get_api_model(self) -> PublicUserModel:
        return PublicUserModel(
            id=self.get_id(),
            discord_id=self.get_discord_id(),
            name=self.get_name(),
            default_platform=self.get_default_platform().get_api_model(),
        )


class Game(BaseModel):
    """
    Game (V2)
    """

    id = AutoField()
    name = CharField()
    steam_id = IntegerField(null=True, default=None)
    sgdb_id = IntegerField(null=True, default=None)
    image_url = CharField(null=True, default=None)
    aliases = ArrayField(TextField, default=lambda: [])  # type: ignore
    release_year = IntegerField(null=True, default=None)
    hidden = BooleanField(default=False)

    def get_id(self) -> int:
        return cast(int, self.id)

    def get_name(self) -> str:
        return cast(str, self.name)

    def get_steam_id(self) -> int | None:
        return cast(int | None, self.steam_id)

    def get_sgdb_id(self) -> int | None:
        return cast(int | None, self.sgdb_id)

    def get_image_url(self) -> str | None:
        return cast(str | None, self.image_url)

    def get_aliases(self) -> list[str]:
        if not self.aliases:
            return []
        return cast(list[str], self.aliases)

    def get_release_year(self) -> int | None:
        return cast(int | None, self.release_year)

    def get_hidden(self) -> bool:
        return cast(bool, self.hidden)

    def set_hidden(self, hidden: bool):
        self.hidden = hidden

    def get_api_model(self) -> PublicGameModel:
        return PublicGameModel(
            id=self.get_id(),
            name=self.get_name(),
            steam_id=self.get_steam_id(),
            sgdb_id=self.get_sgdb_id(),
            image_url=self.get_image_url(),
            aliases=self.get_aliases(),
            release_year=self.get_release_year(),
        )


class Activity(BaseModel):
    """
    Activity (V2)
    """

    id = AutoField()
    timestamp = DateTimeField()
    user = ForeignKeyField(User, backref="activities", on_delete="CASCADE")
    game = ForeignKeyField(Game, backref="activities")
    platform = ForeignKeyField(Platform, backref="activities")
    seconds = IntegerField()
    emulated = BooleanField(default=False)
    hidden = BooleanField(default=False, column_name="hidden")

    def get_id(self) -> int:
        return cast(int, self.id)

    def get_game(self) -> Game:
        return cast(Game, self.game)

    def get_platform(self) -> Platform:
        return cast(Platform, self.platform)

    def get_user(self) -> User:
        return cast(User, self.user)

    def get_seconds(self) -> int:
        return cast(int, self.seconds)

    def get_datetime(self) -> datetime:
        return utils.assertTimezone(self.timestamp)

    def get_timestamp(self) -> int:
        """
        Returns timestamp in milliseconds since epoch
        """
        return int(self.get_datetime().timestamp() * 1000)

    def get_emulated(self) -> bool:
        return cast(bool, self.emulated)

    def get_hidden(self) -> bool:
        return cast(bool, self.hidden)

    def set_hidden(self, hidden: bool):
        self.hidden = hidden

    def get_api_model(self) -> PublicActivityModel:
        return PublicActivityModel(
            id=self.get_id(),
            timestamp=self.get_timestamp(),
            seconds=self.get_seconds(),
            user=self.get_user().get_api_model(),
            game=self.get_game().get_api_model(),
            platform=self.get_platform().get_api_model(),
            emulated=self.get_emulated(),
        )


class LiveActivity(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref="live_activities", on_delete="CASCADE")
    game = ForeignKeyField(Game, backref="live_activities")
    platform = ForeignKeyField(Platform, backref="live_activities")
    started = DateTimeField()

    def get_id(self) -> int:
        return cast(int, self.id)

    def get_user(self) -> User:
        return cast(User, self.user)

    def get_game(self) -> Game:
        return cast(Game, self.game)

    def get_platform(self) -> Platform:
        return cast(Platform, self.platform)

    def get_started_datetime(self) -> datetime:
        return utils.assertTimezone(self.started)

    def get_started_timestamp(self) -> int:
        return int(self.get_started_datetime().timestamp() * 1000)


class DiscordHistory(BaseModel):
    id = AutoField()
    timestamp = DateTimeField(default=lambda: utils.now())
    event = TextField()
    user = CharField(null=True)  # Discord user ID if applicable
    message = TextField()


def connect_db():
    if db.connect():
        logger.info("DB connected")
        db.create_tables([Platform, User, Game, Activity, LiveActivity, DiscordHistory])
        reset_sequences([Platform, Game, Activity, LiveActivity, DiscordHistory, User])


async def clean_loop():
    def cleanupDiscordHistory():
        cutoff = utils.now() - timedelta(days=30)
        logger.info(
            f"Cleaning up DiscordHistory entries older than {cutoff.isoformat()}..."
        )
        deleted = DiscordHistory.delete().where(DiscordHistory.timestamp < cutoff).execute()  # type: ignore
        logger.info(f"Deleted {deleted} old entries from DiscordHistory")

    while True:
        logger.info("Cleaning up... 🧹")
        cleanupDiscordHistory()
        logger.info("Cleanup complete! 🧹")
        await asyncio.sleep(86400)  # every day


def Game_or_none(game_id: int, include_hidden=False) -> Game | None:
    g = Game.get_or_none(Game.id == game_id)
    if g:
        game = cast(Game, g)
        if include_hidden or not game.get_hidden():
            return game
    return None


def User_or_none(user_id: int) -> User | None:
    u = User.get_or_none(User.id == user_id)
    if u:
        return cast(User, u)
    return None


def Activity_or_none(activity_id: int, include_hidden=False) -> Activity | None:
    a = Activity.get_or_none(Activity.id == activity_id)
    if a:
        activity = cast(Activity, a)
        if include_hidden or not activity.get_hidden():
            return activity
    return None


def Platform_or_none(platform_id: int) -> Platform | None:
    p = Platform.get_or_none(Platform.id == platform_id)
    if p:
        return cast(Platform, p)
    return None


def LiveActivity_or_none(
    id: int | None = None, user: User | None = None
) -> LiveActivity | None:
    if id is not None:
        la = LiveActivity.get_or_none(LiveActivity.id == id)
        if la:
            return cast(LiveActivity, la)
    elif user is not None:
        la = LiveActivity.get_or_none(LiveActivity.user == user)
        if la:
            return cast(LiveActivity, la)
    return None
