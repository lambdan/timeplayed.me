import datetime
import logging
import asyncio
from typing import TypedDict, cast

from tpbackend import operations
from tpbackend.discord import bot
from tpbackend.game.select import GameSelect
from tpbackend.globals import MINIMUM_SESSION_LENGTH
from tpbackend.oblivionis import storage
from tpbackend.permissions import Permission
from tpbackend.storage import User, Platform, Game

logger = logging.getLogger("oblivionis-sync")

# PlayStation sessions of exactly 8 hours happen too often, across many users, to be real.
# Probably a bug somewhere outside our control, so they are dropped. Each drop is written
# to the user's history, so they can be looked into later. One guess is the console being
# put in rest mode mid-game, and Sony reporting the time since the game started, capped at 8h
PLAYSTATION_PLATFORMS = ["ps4", "ps5"]
PLAYSTATION_CAPPED_SECONDS = 8 * 60 * 60


class PassedActivity(TypedDict):
    game_name: str
    duration: int
    dt: datetime.datetime
    discord_user_name: str
    discord_user_id: str
    platform: str


def get_game_by_name_or_alias_or_create(s: str, source: str) -> Game:
    game = GameSelect.by_name_or_alias(s)
    if not game:
        # we'll create it!
        # Use create() rather than get_or_create() because name is no longer unique
        # and get_or_create() would raise MultipleObjectsReturned if duplicates exist.
        game = cast(Game, Game.create(name=s))
        logger.info(
            "Added new game '%s' to database (id: %s)", game.get_name(), game.get_id()
        )
        game.add_history(f"Created during {source} sync")
        game.save()
    return game


def parseActivity(
    activity: PassedActivity,
    source: str = "Oblivionis",
    ended: datetime.datetime | None = None,
    details: str = "",
) -> bool:
    """
    Adds a session that ended `ended` (now if None) from Discord activity: from Oblivionis,
    or from the bot's own presence tracking (`source` says which, for logs and history).
    `details` is added to the activity's history (or the user's, if it's dropped)
    """
    try:
        logger.info("Syncing activity: %s", activity)
        if activity["duration"] < MINIMUM_SESSION_LENGTH:
            logger.info("Skipping too short session...")
            return True

        user, created = User.from_discord(
            activity["discord_user_id"], activity["discord_user_name"]
        )
        if created:
            logger.info(
                "Added new user '%s' (id: %s, discord id: %s) to database",
                user.name,
                user.id,
                user.discord_id,
            )
            user.add_history(f"Created during {source} sync")
            user.save()

        # maybe sync names. From Discord, Oblivionis may have an old username
        try:
            user_discord_id = user.get_discord_id()
            if user_discord_id:
                user_info = bot.get_discord_user(user_discord_id)
                if user_info:
                    user.sync_name(user_info.name)
                    user.sync_display_name(user_info.display_name)
        except Exception as e:
            logger.warning(
                "Failed to sync names for user '%s' (id: %s) during sync: %s",
                user.name,
                user.id,
                e,
            )

        if not user.has_permission(Permission.OBLIVIONIS_SYNC):
            logger.warning(
                "User '%s' (id: %s) does not have permission to sync, skipping",
                user.name,
                user.id,
            )
            return True

        if (
            activity["platform"] in PLAYSTATION_PLATFORMS
            and activity["duration"] == PLAYSTATION_CAPPED_SECONDS
        ):
            logger.warning("Skipping PlayStation session of exactly 8 hours...")
            user.add_history(
                f"Dropped {source} activity of exactly 8 hours (game: '{activity['game_name']}', platform: '{activity['platform']}'{details})"
            )
            user.save()
            return True

        incoming_game = activity["game_name"]
        game_name = incoming_game.removesuffix(" with Medal").strip()
        game = get_game_by_name_or_alias_or_create(game_name, source)

        # Discord activity is always on some platform, pc if it didn't say
        incoming_platform = activity["platform"]
        platform_abbr = incoming_platform or "pc"
        if platform_abbr == "pc":
            # apply users set pc platform (pc/win/mac/linux)
            platform_abbr = user.get_pc_platform() or "pc"
        platform, created = Platform.get_or_create(abbreviation=platform_abbr)
        if created:
            logger.info("Added new platform %s to database", platform.abbreviation)
            platform.add_history(f"Created during {source} sync")
            platform.save()

        success = operations.add_session(
            user=user,
            game=game,
            # #62: Discord timestamps cant be trusted, so the end is our own clock (now if None)
            timestamp=ended,
            seconds=activity["duration"],
            platform=platform,
        )
        if success[0]:
            logger.info("Activity synced successfully")
            created_activity = success[0]
            created_activity.add_history(
                f"Activity source: {source} (incoming game: '{incoming_game}', incoming platform: '{incoming_platform}', duration: {activity['duration']}{details})"
            )
            created_activity.save()
            return True

        logger.error("Error when syncing activity: %s", success[1])
        return False
    except Exception as e:
        logger.error("Unhandled exception when syncing: %s", e)
        return False


async def sync_loop():
    while True:
        # logger.info("Checking...")
        oblivionisActivities = storage.Activity.select()
        parsedIds = []

        for o in oblivionisActivities:
            i = o.id
            success = parseActivity(
                {
                    "dt": o.timestamp,
                    "discord_user_name": o.user.name,
                    "discord_user_id": o.user.id,
                    "game_name": o.game.name,
                    "duration": o.seconds,
                    "platform": o.platform,
                }
            )
            if success:
                parsedIds.append(i)

        # delete successful parses
        if len(parsedIds) > 0:
            storage.Activity.delete().where(storage.Activity.id.in_(parsedIds)).execute()  # type: ignore

        await asyncio.sleep(1)
