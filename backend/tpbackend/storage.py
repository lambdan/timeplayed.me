import asyncio
import os
import logging
from typing import cast
from datetime import datetime, timedelta

from peewee import (
    fn,
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
from tpbackend.permissions import DEFAULT_PERMISSIONS

from tpbackend.utils2 import js_iso, now_iso, assertTimezone, now

logger = logging.getLogger("storage_v2")


class CustomDb(PostgresqlExtDatabase):
    def connect(self, reuse_if_open=True):
        connected = super().connect(reuse_if_open)
        if connected:
            # trigger on_connect for all models to do any initialization (like resetting sequences)
            Platform.on_connect()
            User.on_connect()
            Game.on_connect()
            Activity.on_connect()
            LiveActivity.on_connect()
            DiscordHistory.on_connect()
            History.on_connect()

        return connected


db = CustomDb(
    os.environ.get("DB_NAME_TIMEPLAYED"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
)


def reset_sequence(model):
    table = model._meta.table_name
    pk_field = model._meta.primary_key
    sequence_name = f"{table}_{pk_field.name}_seq"
    max_id = model.select(fn.MAX(pk_field)).scalar() or 0
    new_max_id = int(max_id) + 1
    model._meta.database.execute_sql(
        f"SELECT setval('{sequence_name}', {new_max_id}, false);"
    )
    logger.info(f"Reset sequence for {table} to {new_max_id}.")


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def on_connect(cls):
        pass


#################
#### Mixins #####
#################


class IdMixin(BaseModel):
    id = AutoField()

    __has_reset_sequence = False

    def get_id(self) -> int:
        return cast(int, self.id)

    @classmethod
    def on_connect(cls):
        # logger.info(f"{cls.__name__}: on_connect {cls.__has_reset_sequence}")
        if not cls.__has_reset_sequence:
            reset_sequence(cls)
            cls.__has_reset_sequence = True
        super().on_connect()


class HistoryMixin(BaseModel):
    created = DateTimeField(default=lambda: now())
    updated = DateTimeField(default=lambda: now())
    # history = ArrayField(TextField, default=lambda: [])  # type: ignore
    # history is now in a separate table, with foreign key to the model

    pending_history = []

    def save(self, *args, **kwargs):
        self.updated = now()

        # write all pending history
        activity = self.get_id() if isinstance(self, Activity) else None
        game = self.get_id() if isinstance(self, Game) else None
        user = self.get_id() if isinstance(self, User) else None
        platform = self.get_id() if isinstance(self, Platform) else None
        for h in self.pending_history:
            History.create(
                activity=activity,
                game=game,
                user=user,
                platform=platform,
                message=h["message"],
                timestamp=h["timestamp"]
            )
        self.pending_history.clear()

        return super().save(*args, **kwargs)

    def get_created(self) -> datetime:
        return assertTimezone(self.created)

    def get_updated(self) -> datetime:
        # hmm, could just return latest history...
        return assertTimezone(self.updated)

    def get_history(self) -> list[str]:
        # backref
        entries = self.history  # type: ignore
        return [f"[{js_iso(entry.timestamp)}] {entry.message}" for entry in entries]

    def add_history(self, message: str):
        self.pending_history.append({"message": message, "timestamp": now()})


class SearchMixin(BaseModel):
    search = CharField(default="")

    def save(self, *args, **kwargs):
        self.search = self.build_search()[:255]  # varchar(255)
        logger.info(f"Updated search: '{self.search}'")
        return super().save(*args, **kwargs)

    def build_search(self) -> str:
        """
        Return string to be used for searching
        """
        raise NotImplementedError(
            f"missing build_search implementation: {self.__class__.__name__}"
        )


class HiddenMixin(BaseModel):
    hidden = BooleanField(default=False)

    def get_hidden(self) -> bool:
        return cast(bool, self.hidden)

    def set_hidden(self, hidden: bool):
        old_hidden = self.get_hidden()
        self.hidden = cast(BooleanField, hidden)
        # if we have a history mixin, add to history
        if isinstance(self, HistoryMixin):
            self.add_history(f"Hidden changed from {old_hidden} to {hidden}")


####################
###### Models ######
####################


class Platform(IdMixin, HistoryMixin, SearchMixin):
    """
    Platform (V2)
    """

    abbreviation = CharField(unique=True)
    name = CharField(null=True)
    color_primary = CharField(null=True, column_name="color_primary")
    color_secondary = CharField(null=True, column_name="color_secondary")
    icon = CharField(null=True)

    def get_abbreviation(self) -> str:
        return cast(str, self.abbreviation)

    def set_abbreviation(self, abbreviation: str):
        old_abbr = self.get_abbreviation()
        self.abbreviation = abbreviation
        self.add_history(f"Abbreviation changed from '{old_abbr}' to '{abbreviation}'")

    def get_name(self) -> str | None:
        return cast(str | None, self.name)

    def set_name(self, name: str | None):
        old_name = self.get_name()
        self.name = name
        self.add_history(f"Name changed from '{old_name}' to '{name}'")

    def get_color_primary(self) -> str | None:
        return cast(str | None, self.color_primary)

    def set_color_primary(self, color: str | None):
        old_color = self.get_color_primary()
        self.color_primary = color
        self.add_history(f"Primary color changed from '{old_color}' to '{color}'")

    def get_color_secondary(self) -> str | None:
        return cast(str | None, self.color_secondary)

    def set_color_secondary(self, color: str | None):
        old_color = self.get_color_secondary()
        self.color_secondary = color
        self.add_history(f"Secondary color changed from '{old_color}' to '{color}'")

    def get_icon(self) -> str | None:
        return cast(str | None, self.icon)

    def set_icon(self, icon: str | None):
        old_icon = self.get_icon()
        self.icon = icon
        self.add_history(f"Icon changed from '{old_icon}' to '{icon}'")

    def build_search(self) -> str:
        return f"{self.get_id()} {self.get_abbreviation()} {self.get_name() or ''}".strip().lower()


class User(IdMixin, HistoryMixin, SearchMixin):
    """
    User (V2)
    """

    discord_id = CharField(unique=True, null=True)
    name = CharField()
    display_name = CharField(null=True)
    default_platform = ForeignKeyField(
        Platform, default=lambda: Platform.get_or_create(abbreviation="unknown")[0]
    )
    pc_platform = CharField(default="win")
    permissions = ArrayField(TextField, default=lambda: DEFAULT_PERMISSIONS)  # type: ignore

    def get_discord_id(self) -> str | None:
        return cast(str | None, self.discord_id)

    def set_discord_id(self, discord_id: str | None):
        old_discord_id = self.get_discord_id()
        self.discord_id = cast(CharField, discord_id)
        self.add_history(
            f"Discord ID changed from '{old_discord_id}' to '{discord_id}'"
        )

    def get_name(self) -> str:
        return cast(str, self.name)

    def set_name(self, name: str):
        old_name = self.get_name()
        self.name = name
        self.add_history(f"Name changed from '{old_name}' to '{name}'")

    def get_display_name(self) -> str:
        """
        Returns display name if set, otherwise regular name
        """
        if self.display_name:
            return cast(str, self.display_name)
        return self.get_name()

    def set_display_name(self, display_name: str | None):
        old_display_name = self.get_display_name()
        self.display_name = display_name
        self.add_history(
            f"Display name changed from '{old_display_name}' to '{display_name}'"
        )

    def sync_display_name(self, new_display_name: str):
        new_display_name = new_display_name.strip()
        if not new_display_name:
            return
        if new_display_name != self.get_display_name():
            self.set_display_name(new_display_name)
            self.save()
            logger.info(
                "Synced new display name for user %s %s: '%s'",
                self.get_id(),
                self.get_name(),
                new_display_name,
            )
        else:
            logger.info(
                "Display name for user %s %s is already up to date: '%s'",
                self.get_id(),
                self.get_name(),
                new_display_name,
            )

    def get_default_platform(self) -> Platform:
        return cast(Platform, self.default_platform)

    def set_default_platform(self, platform: Platform):
        old_platform = self.get_default_platform()
        self.default_platform = cast(ForeignKeyField, platform)
        self.add_history(
            f"Default platform changed from '{old_platform.abbreviation}' ({old_platform.get_id()}) to '{platform.abbreviation}' ({platform.get_id()})"
        )

    def get_pc_platform(self) -> str:
        return cast(str, self.pc_platform)

    def set_pc_platform(self, pc_platform: str):
        old_pc_platform = self.get_pc_platform()
        self.pc_platform = cast(CharField, pc_platform)
        self.add_history(
            f"PC platform changed from '{old_pc_platform}' to '{pc_platform}'"
        )

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def add_permission(self, permission: str) -> bool:
        """
        Returns true if permission was added, false if user already had permission.
        """
        if not self.has_permission(permission):
            self.permissions.append(permission)  # type: ignore
            self.add_history(f"Added permission '{permission}'")
            return True
        return False

    def remove_permission(self, permission: str) -> bool:
        """
        Returns true if permission was removed, false if user didn't have permission.
        """
        if self.has_permission(permission):
            self.permissions.remove(permission)  # type: ignore
            self.add_history(f"Removed permission '{permission}'")
            return True
        return False

    def get_permissions(self) -> list[str]:
        return cast(list[str], self.permissions)

    def has_activity(self) -> bool:
        # hmm should hidden be filtered here...
        exists = (
            Activity.select()
            .where(
                (Activity.user == self) & (Activity.hidden == False)  # noqa:    E712
            )
            .first()
        )
        return exists is not None

    def build_search(self) -> str:
        return f"{self.get_id()} {self.get_name()} {self.get_display_name()} {self.get_discord_id() or ''}".strip().lower()


class Game(IdMixin, HistoryMixin, SearchMixin, HiddenMixin):
    """
    Game (V2)
    """

    name = CharField()
    sgdb_id = IntegerField(null=True, default=None)
    sgdb_grid_id = IntegerField(null=True, default=None)
    igdb_id = IntegerField(null=True, default=None)
    image_url = CharField(null=True, default=None)
    aliases = ArrayField(TextField, default=lambda: [])  # type: ignore
    release_year = IntegerField(null=True, default=None)
    parent = ForeignKeyField("self", null=True, default=None, backref="children")

    def has_cover_art(self) -> bool:
        if self.get_image_url():
            return True
        if self.get_sgdb_id():
            return True
        if self.get_igdb_id():
            return True
        return False

    def build_search(self) -> str:
        # id + name + release year + all aliases, lowercased
        parts = [f"{self.get_id()}", self.get_name().strip().lower()]
        if self.get_release_year():
            parts.append(str(self.get_release_year()))
        for a in self.get_aliases():
            x = a.strip().lower()
            current = " ".join(parts)
            if x in current:
                continue  # avoid repeating
            parts.append(x)
        new = " ".join(parts)
        return new

    def get_name(self) -> str:
        return cast(str, self.name)

    def set_name(self, name: str):
        old_name = self.get_name()
        self.name = cast(CharField, name)
        self.add_history(f"Name changed from '{old_name}' to '{name}'")

    def get_sgdb_id(self) -> int | None:
        """
        Get SGDB ID (or parents)
        """
        if self.sgdb_id is not None:
            return cast(int, self.sgdb_id)
        # try parent
        parent = self.get_parent()
        if parent:
            return parent.get_sgdb_id()
        return None

    def set_sgdb_id(self, sgdb_id: int | None):
        old_sgdb_id = self.get_sgdb_id()
        self.sgdb_id = cast(IntegerField, sgdb_id)
        self.add_history(f"SGDB ID changed from '{old_sgdb_id}' to '{sgdb_id}'")

    def get_sgdb_grid_id(self) -> int | None:
        """
        Get SGDB grid ID (or parents)
        """
        if self.sgdb_grid_id:
            return cast(int, self.sgdb_grid_id)
        parent = self.get_parent()
        if parent:
            return parent.get_sgdb_grid_id()
        return None

    def set_sgdb_grid_id(self, sgdb_grid_id: int | None):
        old_sgdb_grid_id = self.get_sgdb_grid_id()
        self.sgdb_grid_id = cast(IntegerField, sgdb_grid_id)
        self.add_history(
            f"SGDB grid ID changed from '{old_sgdb_grid_id}' to '{sgdb_grid_id}'"
        )

    def get_igdb_id(self) -> int | None:
        """
        Get IGDB ID (or parents)
        """
        if self.igdb_id is not None:
            return cast(int, self.igdb_id)
        parent = self.get_parent()
        if parent:
            return parent.get_igdb_id()
        return None

    def set_igdb_id(self, igdb_id: int | None):
        old_igdb_id = self.get_igdb_id()
        self.igdb_id = cast(IntegerField, igdb_id)
        self.add_history(f"IGDB ID changed from '{old_igdb_id}' to '{igdb_id}'")

    def get_image_url(self) -> str | None:
        """
        Get image url (or parents)
        """
        if self.image_url:
            return cast(str, self.image_url)
        parent = self.get_parent()
        if parent:
            return parent.get_image_url()
        return None

    def set_image_url(self, image_url: str | None):
        old_image_url = self.get_image_url()
        self.image_url = cast(CharField, image_url)
        self.add_history(f"Image URL changed from '{old_image_url}' to '{image_url}'")

    def get_aliases(self) -> list[str]:
        if not self.aliases:
            return []
        return cast(list[str], self.aliases)

    def add_alias(self, alias: str) -> bool:
        aliases = self.get_aliases()
        if alias not in aliases:
            self.aliases.append(alias)  # type: ignore
            self.add_history(f"Added alias '{alias}'")
            return True
        return False

    def remove_alias(self, alias: str) -> bool:
        aliases = self.get_aliases()
        if alias in aliases:
            self.aliases.remove(alias)  # type: ignore
            self.add_history(f"Removed alias '{alias}'")
            return True
        return False

    def get_release_year(self) -> int | None:
        return cast(int | None, self.release_year)

    def set_release_year(self, release_year: int | None):
        old_release_year = self.get_release_year()
        self.release_year = cast(IntegerField, release_year)
        self.add_history(
            f"Release year changed from '{old_release_year}' to '{release_year}'"
        )

    def get_hidden(self) -> bool:
        # hide if parent is hidden
        parent = self.get_parent()
        if parent and parent.get_hidden():
            return True
        return super().get_hidden()

    def get_parent(self) -> "Game | None":
        return cast(Game | None, self.parent)

    def set_parent(self, new_parent: "Game | None"):
        if new_parent == self.get_parent():
            raise ValueError("No change")
        if new_parent:
            # avoid self
            if self.get_id() == new_parent.get_id():
                raise ValueError("Game cannot be its own parent")
            # avoid setting parent to a child
            children = self.get_children()
            if any(c.get_id() == new_parent.get_id() for c in children):
                raise ValueError("Game cannot be parent of a child")
        old_parent = self.get_parent()
        old_parent_name = "None"
        if old_parent:
            old_parent_name = f"'{old_parent.get_name()}' ({old_parent.get_id()})"
        self.parent = cast(ForeignKeyField, new_parent)
        new_parent_name = "None"
        if new_parent:
            new_parent_name = f"'{new_parent.get_name()}' ({new_parent.get_id()})"
        self.add_history(f"Parent changed from {old_parent_name} to {new_parent_name}")

    def get_children(self, recursive=True) -> list["Game"]:
        children = []
        for c in cast(list[Game], list(self.children)):  # type: ignore
            children.append(c)
            if recursive:
                for cc in c.get_children():
                    children.append(cc)
        return children

    def user_has_played(self, user: User) -> bool:
        exists = (
            Activity.select()
            .where(
                (Activity.game == self)
                & (Activity.user == user)
                & (Activity.hidden == False)  # noqa: E712
            )
            .first()
        )
        return exists is not None

    def platform_has_played(self, platform: Platform) -> bool:
        exists = (
            Activity.select()
            .where(
                (Activity.game == self)
                & (Activity.platform == platform)
                & (Activity.hidden == False)  # noqa: E712
            )
            .first()
        )
        return exists is not None


class Activity(IdMixin, HistoryMixin, HiddenMixin):
    """
    Activity (V2)
    """

    timestamp = DateTimeField()
    user = ForeignKeyField(User, backref="activities", on_delete="CASCADE")
    game = ForeignKeyField(Game, backref="activities")
    platform = ForeignKeyField(Platform, backref="activities")
    seconds = IntegerField()
    emulated = BooleanField(default=False)

    def get_game(self) -> Game:
        return cast(Game, self.game)

    def set_game(self, game: Game):
        old_game = self.get_game()
        self.game = cast(ForeignKeyField, game)
        self.add_history(
            f"Game changed from '{old_game.get_name()}' ({old_game.get_id()}) to '{game.get_name()}' ({game.get_id()})"
        )

    def get_platform(self) -> Platform:
        return cast(Platform, self.platform)

    def set_platform(self, platform: Platform):
        old_platform = self.get_platform()
        self.platform = cast(ForeignKeyField, platform)
        self.add_history(
            f"Platform changed from '{old_platform.abbreviation}' ({old_platform.get_id()}) to '{platform.abbreviation}' ({platform.get_id()})"
        )

    def get_user(self) -> User:
        return cast(User, self.user)

    def set_user(self, user: User):
        old_user = self.get_user()
        self.user = cast(ForeignKeyField, user)
        self.add_history(
            f"User changed from '{old_user.get_name()}' ({old_user.get_id()}) to '{user.get_name()}' ({user.get_id()})"
        )

    def get_seconds(self) -> int:
        return cast(int, self.seconds)

    def set_seconds(self, seconds: int):
        old_seconds = self.get_seconds()
        self.seconds = cast(IntegerField, seconds)
        self.add_history(f"Seconds changed from {old_seconds} to {seconds}")

    def get_datetime(self) -> datetime:
        return assertTimezone(self.timestamp)

    def set_datetime(self, dt: datetime):
        old_date = self.get_datetime()
        self.timestamp = cast(DateTimeField, dt)
        self.add_history(f"Timestamp changed from {js_iso(old_date)} to {js_iso(dt)}")

    def get_timestamp(self) -> int:
        """
        Returns timestamp in milliseconds since epoch
        """
        return int(self.get_datetime().timestamp() * 1000)

    def get_emulated(self) -> bool:
        return cast(bool, self.emulated)

    def set_emulated(self, emulated: bool):
        old_emulated = self.get_emulated()
        self.emulated = cast(BooleanField, emulated)
        self.add_history(f"Emulated changed from {old_emulated} to {emulated}")


class LiveActivity(IdMixin):
    user = ForeignKeyField(User, backref="live_activities", on_delete="CASCADE")
    game = ForeignKeyField(Game, backref="live_activities")
    platform = ForeignKeyField(Platform, backref="live_activities")
    started = DateTimeField()

    def get_user(self) -> User:
        return cast(User, self.user)

    def get_game(self) -> Game:
        return cast(Game, self.game)

    def get_platform(self) -> Platform:
        return cast(Platform, self.platform)

    def get_started_datetime(self) -> datetime:
        return assertTimezone(self.started)

    def get_started_timestamp(self) -> int:
        return int(self.get_started_datetime().timestamp() * 1000)


class DiscordHistory(IdMixin):
    timestamp = DateTimeField(default=lambda: now())
    event = TextField()
    user = CharField(null=True)  # Discord user ID if applicable
    message = TextField()


class History(IdMixin):
    timestamp = DateTimeField(default=lambda: now())
    game = ForeignKeyField(Game, backref="history", null=True)
    user = ForeignKeyField(User, backref="history", null=True)
    platform = ForeignKeyField(Platform, backref="history", null=True)
    activity = ForeignKeyField(Activity, backref="history", null=True)
    message = TextField()


async def clean_loop():
    def cleanupDiscordHistory():
        cutoff = now() - timedelta(days=30)
        logger.info(
            f"Cleaning up DiscordHistory entries older than {cutoff.isoformat()}..."
        )
        deleted = DiscordHistory.delete().where(DiscordHistory.timestamp < cutoff).execute()  # type: ignore
        logger.info(f"Deleted {deleted} old entries from DiscordHistory")

    while True:
        logger.info("Cleaning up... 🧹")
        cleanupDiscordHistory()
        logger.info("Cleanup complete! 🧹")
        await asyncio.sleep(3600)  # every hour


def User_or_none(user_id: str | int | None) -> User | None:
    if user_id is None:
        return None
    u = User.get_or_none(User.id == int(user_id))
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


def Platform_or_none(platform_id: int | str | None) -> Platform | None:
    if platform_id is None:
        return None
    p = Platform.get_or_none(Platform.id == int(platform_id))
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
