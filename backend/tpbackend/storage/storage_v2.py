import os
import logging

from tpbackend import utils
from tpbackend.permissions import PERMISSION_COMMANDS
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
    permissions = ArrayField(TextField, default=lambda: [PERMISSION_COMMANDS])  # type: ignore

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


class LiveActivity(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref="live_activities", on_delete="CASCADE")
    game = ForeignKeyField(Game, backref="live_activities")
    platform = ForeignKeyField(Platform, backref="live_activities")
    started = DateTimeField()


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
