import datetime
import json
import logging
import asyncio
from typing import TypedDict

from tpbackend import operations
from tpbackend.consts import MINIMUM_SESSION_LENGTH
from tpbackend.oblivionis import storage
from tpbackend.storage.storage_v2 import User, Game, Platform, Activity

logger = logging.getLogger("oblivionis-sync")


class PassedActivity(TypedDict):
    game_name: str
    duration: int
    dt: datetime.datetime
    user_name: str
    user_id: int
    platform: str


def parseActivity(activity: PassedActivity) -> bool:
    try:
        logger.info("Syncing activity: %s", activity)
        if activity["duration"] < MINIMUM_SESSION_LENGTH:
            logger.info("Skipping too short session...")
            return True

        user, created = User.get_or_create(
            id=activity["user_id"], name=activity["user_name"]
        )
        if created:
            logger.info("Added new user %s to database", user.name)

        game_name = activity["game_name"]
        game_name = game_name.removesuffix(" with Medal").strip()
        game = Game.get_or_none(name=game_name)
        # if game not found, try by alias
        if game is None:
            game = operations.get_game_by_alias(game_name)
            if game:
                logger.info("Found game %s by alias!", game.name)
        # if still none, create it
        if game is None:
            logger.info("Did not find game %s by name or alias, creating...", game_name)
            game, created = Game.get_or_create(name=game_name)
            if created:
                logger.info("Added new game %s to database", game.name)

        platform_abbr = activity["platform"]
        if platform_abbr == "pc":
            platform_abbr = user.pc_platform
        platform, created = Platform.get_or_create(abbreviation=platform_abbr)
        if created:
            logger.info("Added new platform %s to database", platform.abbreviation)

        success = operations.add_session(
            user=user,
            game=game,
            timestamp=activity["dt"],
            seconds=activity["duration"],
            platform=platform,
        )
        if success[0]:
            logger.info("Activity synced successfully")
            return True

        logger.error("Error when syncing activity: %s", success[1])
        return False
    except Exception as e:
        logger.error("Unhandled exception when syncing: %s", e)
        return False


async def start():
    while True:
        oblivionisActivities = storage.Activity.select()
        parsedIds = []

        for o in oblivionisActivities:
            i = o.id
            success = parseActivity(
                {
                    "dt": o.timestamp,
                    "user_name": o.user.name,
                    "user_id": o.user.id,
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

        await asyncio.sleep(5)
