import datetime
import logging
import asyncio
from typing import TypedDict, cast

from tpbackend import operations
from tpbackend.discord import bot
from tpbackend.game.select import GameSelect
from tpbackend.globals import MINIMUM_SESSION_LENGTH
from tpbackend.oblivionis import storage
from tpbackend.permissions import PERMISSION_OBLIVIONIS_SYNC
from tpbackend.storage import User, Platform, Game

logger = logging.getLogger("oblivionis-sync")


class PassedActivity(TypedDict):
    game_name: str
    duration: int
    dt: datetime.datetime
    discord_user_name: str
    discord_user_id: str
    platform: str


def get_game_by_name_or_alias_or_create(s: str, creation_message: str) -> Game:
    game = GameSelect.by_name_or_alias(s)
    if game:
        return game
    # OK FINE we'll create it!
    # Use create() rather than get_or_create() because name is no longer unique
    # and get_or_create() would raise MultipleObjectsReturned if duplicates exist.
    game = Game.create(name=s)  # type: ignore
    logger.info("Added new game '%s' to database (id: %s)", game.name, game.id)

    g = GameSelect.by_id(game.id)
    if g:
        g.add_history(creation_message)
        g.save()

    # this shouldnt be possible...
    raise Exception("Created game not found?!")


def parseActivity(activity: PassedActivity) -> bool:
    try:
        logger.info("Syncing activity: %s", activity)
        if activity["duration"] < MINIMUM_SESSION_LENGTH:
            logger.info("Skipping too short session...")
            return True

        user_name = activity["discord_user_name"]
        user, created = User.get_or_create(
            discord_id=activity["discord_user_id"],
            name=user_name,
        )
        if created:
            logger.info(
                "Added new user '%s' (id: %s, discord id: %s) to database",
                user.name,
                user.id,
                user.discord_id,
            )
            user.add_history("Created during Oblivionis sync")
            user.save()

        user = cast(User, user)
        user_info = bot.user_info_from_discord_user_id(user.get_id())
        if user_info:
            user.sync_display_name(user_info.display_name)

        if not user.has_permission(PERMISSION_OBLIVIONIS_SYNC):
            logger.warning(
                "User '%s' (id: %s) does not have permission to sync, skipping",
                user.name,
                user.id,
            )
            return True

        game_name = activity["game_name"]
        game_name = game_name.removesuffix(" with Medal").strip()

        game = get_game_by_name_or_alias_or_create(
            game_name, "Created during Oblivionis sync"
        )

        platform_abbr = activity["platform"]
        if platform_abbr == "pc":
            platform_abbr = user.pc_platform
        platform, created = Platform.get_or_create(abbreviation=platform_abbr)
        if created:
            logger.info("Added new platform %s to database", platform.abbreviation)
            platform.add_history("Created during Oblivionis sync")
            platform.save()

        success = operations.add_session(
            user=user,
            game=game,
            # #62: Discord timestamps cant be trusted... passing None to let it default to now
            # timestamp=activity["dt"],
            seconds=activity["duration"],
            platform=platform,
        )
        if success[0]:
            logger.info("Activity synced successfully")
            created_activity = success[0]
            created_activity.add_history("Activity source: Oblivionis")
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
