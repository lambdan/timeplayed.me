import os
import logging
from typing import cast

from tpbackend import utils
from tpbackend.permissions import DEFAULT_PERMISSIONS
from tpbackend.storage.reset_sequence import reset_sequences

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

    def get_default_platform(self) -> Platform:
        return cast(Platform, self.default_platform)

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

    def get_hidden(self) -> bool:
        return cast(bool, self.hidden)

    def set_hidden(self, hidden: bool):
        self.hidden = hidden
        self.save()


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
    auto_hidden = BooleanField(default=False, column_name="auto_hidden")
    # manual hidden in the future?

    def get_id(self) -> int:
        return cast(int, self.id)

    def get_game(self) -> Game:
        return cast(Game, self.game)

    def get_platform(self) -> Platform:
        return cast(Platform, self.platform)

    def get_user(self) -> User:
        return cast(User, self.user)

    def is_hidden(self) -> bool:
        return cast(bool, self.auto_hidden)


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


def Game_or_none(game_id: int) -> Game | None:
    g = Game.get_or_none(Game.id == game_id)
    if g:
        return cast(Game, g)
    return None


def User_or_none(user_id: int) -> User | None:
    u = User.get_or_none(User.id == user_id)
    if u:
        return cast(User, u)
    return None


def Activity_or_none(activity_id: int) -> Activity | None:
    a = Activity.get_or_none(Activity.id == activity_id)
    if a:
        return cast(Activity, a)
    return None


def Platform_or_none(platform_id: int) -> Platform | None:
    p = Platform.get_or_none(Platform.id == platform_id)
    if p:
        return cast(Platform, p)
    return None
