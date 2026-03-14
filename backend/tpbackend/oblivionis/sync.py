import datetime
import logging
import asyncio
from typing import TypedDict

from tpbackend import operations
from tpbackend.consts import MINIMUM_SESSION_LENGTH
from tpbackend.oblivionis import storage
from tpbackend.storage.storage_v2 import User, Platform

logger = logging.getLogger("oblivionis-sync")

# TODO: store in database so admins can add easily
IGNORED_GAMES = [
    "Medal",
    "YouTube",
    "Blender",
    "CurseForge",
    "Steam",
    "Discord",
    "Epic Games Launcher",
    "YouTube VR",
    "YouTube Music",
    "Spotify",
    "Krita",
]


class PassedActivity(TypedDict):
    game_name: str
    duration: int
    dt: datetime.datetime
    discord_user_name: str
    discord_user_id: str
    platform: str


def parseActivity(activity: PassedActivity) -> bool:
    try:
        logger.info("Syncing activity: %s", activity)
        if activity["duration"] < MINIMUM_SESSION_LENGTH:
            logger.info("Skipping too short session...")
            return True

        user, created = User.get_or_create(
            discord_id=activity["discord_user_id"], name=activity["discord_user_name"]
        )
        if created:
            logger.info(
                "Added new user '%s' (id: %s, discord id: %s) to database",
                user.name,
                user.id,
                user.discord_id,
            )

        game_name = activity["game_name"]
        game_name = game_name.removesuffix(" with Medal").strip()

        if game_name in IGNORED_GAMES:
            logger.info("Ignoring game (app) '%s'", game_name)
            return True

        game = operations.get_game_by_name_or_alias_or_create(game_name)

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

        await asyncio.sleep(5)
