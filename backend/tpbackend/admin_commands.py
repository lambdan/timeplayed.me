import datetime
import discord

from tpbackend import commands, operations, utils
from tpbackend.storage.storage_v2 import Activity, Game, Platform, User

APP_STARTED = datetime.datetime.now(datetime.UTC)

ADMIN_HELP = """☢️
## Games
- `!addgame <name>`
- `!delgame <game_id>`
- `!addalias <game_id> <alias>`
- `!delalias <game_id> <alias>`
- `!setgameimage <game_id> <url|null>`
- `!setsteamid <game_id> <steam_id|null>`
- `!setsgdbid <game_id> <sgdb_id|null>`

## Platforms: 

- `!setgamereleaseyear <game_id> <year>`
- `!addplatform <platform_abbreviation> <platform_name>`
- `!delplatform <platform_abbreviation>`

## Activity:

- `!adm_remove <activity_id>`
- `!adm_setgame <activity_id> <game_id>`

## Users:

- `!users`
- `!toggleblockcommands <user_id>`

## Misc

- `!uptime`
"""


def adm_tree(
    message: discord.Message, user: User, first: str, content: str
) -> str | None:
    """
    Admin command dispatcher. Returns None if the command is not recognized.
    """
    if first == "!help_admin":
        return ADMIN_HELP
    elif first == "!setgameimage":
        return adm_set_game_image(content)
    elif first == "!setsteamid":
        return adm_set_steam_id(content)
    elif first == "!setsgdbid":
        return adm_set_sgdb_id(content)
    elif first == "!addalias":
        return adm_add_alias(content)
    elif first == "!delalias":
        return adm_del_alias(content)
    elif first == "!setgamereleaseyear":
        return adm_set_game_release_year(content)
    elif first == "!addplatform":
        return adm_add_platform(content)
    elif first == "!delplatform":
        return adm_del_platform(content)
    elif first == "!adm_remove":
        return adm_delete_activity(content)
    elif first == "!adm_setgame":
        return adm_set_game(content)
    elif first == "!toggleblockcommands":
        return adm_toggle_block_commands(user, content)
    elif first == "!addgame":
        content = commands.try_expand_alias(content)
        return adm_add_game(content)
    elif first == "!delgame":
        return adm_del_game(content)
    elif first == "!users":
        return adm_list_users()
    elif first == "!uptime":
        started = APP_STARTED
        duration = datetime.datetime.now(datetime.UTC) - started
        return f"Bot uptime: {utils.secsToHHMMSS(int(duration.total_seconds()))}"
    return None


def adm_set_game_image(message: str) -> str:
    # !setgameimage <game_id> <image_url|null>
    # same url for both for now
    parts = message.removeprefix("!setgameimage ").strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setgameimage <game_id> <image_url>`"
    game = Game.get_or_none(Game.id == int(parts[0]))  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {parts[0]} not found."
    image_url = parts[1]
    if image_url != "null" and not image_url.startswith("http"):
        return "ERROR: Image URL should start with http or https, or be null"
    game.image_url = None if image_url == "null" else image_url
    game.save()
    return f"OK, updated game image for game **{game.name}**"


def adm_set_steam_id(message: str) -> str:
    # !setsteamid <game:id> <steam_id>
    parts = message.removeprefix("!setsteamid ").strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setsteamid <game_id> <steam_id>`"
    game_id = int(parts[0])
    steam_id = None if parts[1] == "null" else int(parts[1])
    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    Game.update(steam_id=steam_id).where(Game.id == game.id).execute()  # type: ignore
    return f"OK! Set Steam ID {steam_id} for game {game.name}"


def adm_set_sgdb_id(message: str) -> str:
    # !setsgdbid <game:id> <sgdb_id>
    parts = message.removeprefix("!setsgdbid ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format"
    game_id = int(parts[0])
    sgdb_id = None if parts[1] == "null" else int(parts[1])
    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    Game.update(sgdb_id=sgdb_id).where(Game.id == game.id).execute()  # type: ignore
    return f"OK! **{game.name}** SGDB ID = **{sgdb_id}**"


def adm_add_alias(message: str) -> str:
    # !addalias <game_id> <alias>
    parts = message.removeprefix("!addalias ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format. Use: `!addalias <game_id> <alias>`"
    game_id = int(parts.pop(0))
    alias = " ".join(parts).strip()

    # check if any game already uses this alias
    aliasedGame = operations.get_game_by_alias(alias)
    if aliasedGame:
        return f"ERROR: Alias '{alias}' already exists for game {aliasedGame.name} (ID {aliasedGame})."

    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    if game.aliases and alias in game.aliases:
        return f"Alias '{alias}' already exists for game {game.name}."
    if not game.aliases:
        game.aliases = []
    game.aliases.append(alias)
    game.save()
    return f"OK! Added alias '{alias}' for game {game.name}"


def adm_del_alias(message: str) -> str:
    # !delalias <game_id> <alias>
    parts = message.removeprefix("!delalias ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format. Use: `!delalias <game_id> <alias>`"
    game_id = int(parts.pop(0))
    alias = " ".join(parts).strip()
    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    if not game.aliases or alias not in game.aliases:
        return f"Alias '{alias}' does not exist for game {game.name}."
    game.aliases.remove(alias)
    game.save()
    return f"OK! Removed alias '{alias}' from game {game.name}"


def adm_set_game_release_year(message: str) -> str:
    # !setgamereleaseyear <game_id> <year>
    parts = message.removeprefix("!setgamereleaseyear ").strip().split()
    if len(parts) != 2:
        return (
            "ERROR: Invalid command format. Use: `!setgamereleaseyear <game_id> <year>`"
        )
    game_id = int(parts[0])
    year = int(parts[1])

    year_now = datetime.datetime.now(datetime.UTC).year
    if year < 1950 or year > year_now:
        return f"ERROR: Invalid year {year}. It should be between 1950 and {year_now}."

    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."

    game.release_year = year
    game.save()
    return f"OK! Set release year {year} for game {game.name}"


def adm_add_platform(message: str) -> str:
    # !addplatform <platform_abbreviation> <platform_name>
    parts = message.removeprefix("!addplatform ").strip().split()

    if len(parts) < 2:
        return "ERROR: Invalid command format. Use: `!addplatform <platform_abbreviation> <platform_name>`"

    abbr = parts.pop(0)
    name = " ".join(parts).strip()

    reply = []
    platform, created = Platform.get_or_create(abbreviation=abbr)
    if created:
        reply.append("Added new platform")
    platform.name = name if len(name) > 0 else None
    platform.save()
    reply.append(f"Abbreviation: **{abbr}**, Name: **{name}**")
    return "\n".join(reply)


def adm_del_platform(message: str) -> str:
    # !delplatform <platform_abbreviation>
    parts = message.removeprefix("!delplatform ").strip().split()
    abbr = parts[0].strip()

    platform = Platform.get_or_none(Platform.abbreviation == abbr)
    if platform is None:
        return "Platform not found"

    platform.delete_instance()
    return "OK, deleted platform " + abbr


def adm_delete_activity(message: str) -> str:
    # !adm_remove <activity_id>
    i = int(message.split()[1].strip())
    activity = Activity.get_or_none(Activity.id == i)  # type: ignore
    if activity is None:
        return f"ERROR: Activity with ID {i} not found."
    activity.delete_instance()
    return f"OK! Deleted activity {i}"


def adm_set_game(message: str) -> str:
    # !adm_setgame <activity_id> <game_id>
    msg = message.removeprefix("!adm_setgame ").strip().split()
    if len(msg) != 2:
        return (
            "ERROR: Invalid command format. Use: `!adm_setgame <activity_id> <game_id>`"
        )
    activity_id = int(msg[0])
    game_id = int(msg[1])
    activity = Activity.get_or_none(Activity.id == activity_id)  # type: ignore
    if activity is None:
        return f"ERROR: Activity with ID {activity_id} not found."
    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    activity.game = game
    activity.save()
    return f"OK! Set activity {activity_id} game to {game.id} ({game.name})"


def adm_toggle_block_commands(requester: User, message: str) -> str:
    # !adm_toggleblockcommands <user_id>
    i = int(message.split()[1].strip())
    user = User.get_or_none(User.id == i)
    if user is None:
        return f"ERROR: User with ID {i} not found."
    if requester.id == user.id:
        return "ERROR: You cannot block yourself :)"
    user.bot_commands_blocked = not user.bot_commands_blocked
    user.save()
    status = "blocked 🛑" if user.bot_commands_blocked else "unblocked ✅"
    return (
        f"OK! User {user.name} (ID {user.id}) is now {status} from using bot commands."
    )


def adm_add_game(message: str) -> str:
    # !addgame <name>
    name = message.removeprefix("!addgame ").strip()
    if len(name) == 0:
        return "ERROR: Invalid command format. Use: `!addgame <name>` (no quotes)"
    sanitized = utils.sanitize(name)
    if sanitized != name:
        return "Game name invalid"

    # check if any game already uses this name
    existingGame = Game.get_or_none(Game.name == name)
    if existingGame:
        return (
            f"ERROR: Game with name '{name}' already exists with ID {existingGame.id}."
        )

    game = Game.create(name=name)
    return f"OK! Added new game **{game.name}** with ID {game.id}"


def adm_del_game(msg: str) -> str:
    i = int(msg.split()[1].strip())
    game = Game.get_or_none(Game.id == i)  # type: ignore
    if game is None:
        return f"ERROR: Game with ID {i} not found."
    activities = Activity.select().where(Activity.game == game)
    if activities.count() > 0:
        return f"ERROR: Cannot delete game {game.name} because it has activities"
    game.delete_instance()
    return f"OK! Deleted game {i}"


def adm_list_users() -> str:
    users = User.select()
    # - 123456789 | **djs** | admin  ✅❌ | bot_commands_blocked ✅❌
    # - 123456789123456789 | **someoneelse** | admin  ✅❌ | bot_commands_blocked ✅❌
    out = ""
    for user in users:
        admin = "admin " + ("✅" if commands.is_admin(user) else "❌")
        commandsBlocked = "bot_commands_blocked " + (
            "✅" if user.bot_commands_blocked else "❌"
        )
        out += f"- `{user.id}` **{user.name}** :: {admin} :: {commandsBlocked}\n"
    return out
