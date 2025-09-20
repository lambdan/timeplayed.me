import datetime
import logging
import discord
from tpbackend import admin_commands, operations, utils, consts
from tpbackend.storage.storage_v2 import LiveActivity, User, Game, Platform, Activity

from tpbackend.globals import ADMINS

logger = logging.getLogger("commands")

def dm_help(isAdmin: bool) -> str:
    base = """
# Datetime 📆
- Anywhere a datetime is expected, you can use ISO8601 format (e.g. `2023-10-01T12:00:00Z`) or relative time (e.g. `-1h30m5s`)
- Typically if its omitted it will default to now

# Manual entries:
- `!add "Game Name"|alias <duration> [datetime]` - Add a session of specified duration
- `!start "Game Name"|alias [platform] [datetime]`
- `!stop` - Stop the current manually started session
- `!time` - Show the current running session time (if any)

# Maintenance:
- `!last [n]` - Shows your last n sessions (default is 1, max is 10)
- `!merge <game_id1> <game_id2>` - Merge game_id1 into game_id2 (only affects your sessions)
- `!remove <session_id>` - Remove session with id
- `!setdate <session_id> <datetime>` - Change date of a session

## Platforms: 
- `!platform` - Show your current default platform
- `!platform <name>` - Set your default platform
- `!platforms` - List all valid platforms
- `!setplatform <session_id> <platform>`
- `!setplatform <session_id1-session_id2> <platform>` 

## Games:
- `!game <game_id|game_name>` 
- `!search <query>`
- `!setgame <session_id> "Game Name"` 
- `!setgame <session_id1-session_id2> "Game Name"` 
"""
    
    if isAdmin:
        return base + "\n\n☢️ You are admin, use `!help_admin` for admin commands"
    return base




def user_from_message(message: discord.Message) -> User | None:
    if message.author is None:
        return None
    user, created = User.get_or_create(id=message.author.id, name=message.author.name)
    if created:
        logger.info("Added new user %s %s to database", message.author.id, message.author.name)
    return user

def user_name_from_message(message: discord.Message) -> str:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.name

def dm_add_session(user: User, msg: str) -> str:
    # !add "Game Name" <duration> [timestamp|relative_time]

    splitted = msg.split(' ')
    timestamp = utils.now()
    duration = 0

    last = splitted.pop().strip()
    while not last.endswith('"'): # while not hitting the game name
        if last.endswith("Z") or last.startswith("-"):
            timestamp = utils.datetimeParse(last)
            if timestamp is None:
                return "Invalid timestamp format"
        else:
            duration = utils.secsFromString(last)
            if duration is None:
                return "Invalid duration format"
        last = splitted.pop().strip()
    
    msg = msg.removeprefix('!add "') # remove first quote
    gameName = msg.split('"')[0].strip() # game name from last quote
    
    game, created = Game.get_or_create(name=gameName)
    if created:
        logger.info("Added new game %s to database", gameName)
    
    result = operations.add_session(
                    user=user,
                    game=game,
                    seconds=duration, 
                    timestamp=timestamp)
    sesh = result[0]
    if sesh:
        return f"Session #{sesh} saved.\nYou played **{ game.name }** for {utils.secsToHHMMSS(int(str(sesh.seconds)))} at {timestamp.isoformat().split('.')[0]} UTC"
    return f"ERROR: {result[1]}"

def dm_start_session(user: User, msg: str) -> str:
    # !start "Game Name" <platform> <datetime|relative_time>
    runningSession = LiveActivity.get_or_none(LiveActivity.user == user)
    if runningSession:
        return "You already have a session running. Use `!stop` to end it first."

    splitted = msg.split(' ')
    timestamp = utils.now()
    platform = user.default_platform

    last = splitted.pop().strip() 
    while not last.endswith('"'):
        if last.endswith("Z") or last.startswith("-"):
            timestamp = utils.datetimeParse(last)
            if timestamp is None:
                return "Invalid timestamp format"
        else:
            platform = Platform.get_or_none(Platform.abbreviation == last.lower())
            if not platform:
                return "Invalid platform"
        last = splitted.pop().strip()
    
    msg = msg.removeprefix('!start "')
    gameName = msg.split('"')[0].strip()
        
    game, created = Game.get_or_create(name=gameName)
    if created:
        logger.info("Added new game %s to database", gameName)

    live = LiveActivity.create(
        user=user,
        game=game,
        platform=platform,
        started=timestamp
    )
    return f"⏱️ Started playing **{game.name}** on **{platform.abbreviation}** at {timestamp.isoformat()}.\nSend `!stop` to end the session."

def dm_stop_session(user: User, message: discord.Message) -> str:
    # !stop
    live = LiveActivity.get_or_none(LiveActivity.user == user)
    if not live:
        return "You don't have a session running"
    
    started: datetime.datetime = live.started
    if started.tzinfo is None:
        # tz info is lost in the database, assume UTC
        started = started.replace(tzinfo=datetime.timezone.utc)
    duration = utils.now() - started
    seconds = int(duration.total_seconds())

    result = operations.add_session(
                user=user,
                platform=live.platform,
                game=live.game,
                seconds=seconds)
    
    sesh = result[0]
    live.delete_instance()  # Remove the live session from db
    if sesh:
        return f"✅ Session #{sesh} saved.\nYou played **{ sesh.game.name }** on **{ sesh.platform.abbreviation }** for {utils.secsToHHMMSS(int(str(sesh.seconds)))}"
    
    if isinstance(result[1], ValueError):
        return "Session ended, but not saved because it was too short"
    
    return "Something went wrong..."

def dm_time_session(user: User, message: discord.Message) -> str:
    # !time
    live = LiveActivity.get_or_none(LiveActivity.user == user)
    if not live:
        return "You don't have a session running"
    
    started: datetime.datetime = live.started
    if started.tzinfo is None:
        # tz info is lost in the database, assume UTC
        started = started.replace(tzinfo=datetime.timezone.utc)
    
    duration = utils.now() - started
    seconds = int(duration.total_seconds())
    
    return f"⏱️ You have been playing for {utils.secsToHHMMSS(seconds)}. \nSend `!stop` to end the session."

def dm_merge_game(user: User, message: discord.Message) -> str:
    # !merge 123 456 
    parts = message.content.removeprefix('!merge ').strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!merge game_id1 game_id2`"
    game_id1 = int(parts[0])
    game_id2 = int(parts[1])
    return operations.merge_games(user, gameId1=game_id1, gameId2=game_id2)

def dm_remove_session(user: User, message: discord.Message) -> str:
    # !remove session_id
    msg = message.content.removeprefix('!remove ').strip()
    if not msg.isdigit():
        return "Invalid command format (not a number?)"
    msg = int(msg)
    return operations.remove_session(user, sessionId=msg)

def dm_platform(user: User, message: discord.Message) -> str:
    if message.content == "!platform":
        return f"Your default platform is **{user.default_platform.abbreviation}**. Use `!platform <name>` to change it."
    
    platform = message.content.removeprefix('!platform ').strip().lower()
    platform = Platform.get_or_none(Platform.abbreviation == platform)
    if not platform:
        return "Invalid platform. Use `!listplatforms` to see valid platforms, or ask an admin to add it."

    user,created = User.get_or_create(id=message.author.id, name=message.author.name)
    user.default_platform = platform
    user.save()
    return f"Your default platform has been set to **{user.default_platform.abbreviation}**"

def dm_set_platform(user: User, message: discord.Message) -> str:
    # !setplatform <session_id> <platform>
    parts = message.content.removeprefix('!setplatform ').strip().split()
    if len(parts) != 2:
        return "Invalid command format"
    
    session_id = parts[0]
    platform = parts[1].lower()

    platform = Platform.get_or_none(Platform.abbreviation == platform)
    if not platform:
        return "Invalid platform"

    parsed = utils.parseRange(session_id)
    if parsed:
        a,b = parsed
    else:
        try:
            a = int(session_id)
            b = a
        except ValueError:
            return "Invalid session ID. Please provide a valid integer or a range in the format `start-end`."
    successes = 0
    while a <= b:
        if operations.set_platform_for_session(
            user,
            sessionId=a,
            platform=platform):
            successes += 1
        a += 1
    return f"Platform updated on {successes} session(s)"


def dm_set_date(user: User, message: discord.Message) -> str:
    # !setdate <session_id> <new_date>
    parts = message.content.removeprefix('!setdate ').strip().split()
    if len(parts) != 2:
        return "Invalid format"
    
    session_id = int(parts[0])
    new_date = utils.datetimeParse(parts[1])
    if new_date is None:
        return "Date format is invalid"
    
    return operations.modify_session_date(
            user,
            sessionId=session_id,
            new_date=new_date
        )

def dm_last_sessions(user: User, message: discord.Message) -> str:
    # !last
    # !last n
    splitted = message.content.split()
    amount = 1
    if len(splitted) == 2:
        amount = min(int(splitted[1]), 10)
    sessions = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.desc()).limit(amount)
    lines = []
    for session in sessions:
        lines.append(f"#{session}\t{session.timestamp.isoformat().split(".")[0].replace("T"," ")} UTC\t{session.game.name} ({session.platform.abbreviation})\t{utils.secsToHHMMSS(session.seconds)}")
    out = "```\n"
    out += "\n".join(reversed(lines))
    out += "```"
    return out
    
def dm_set_game(user: User, message: discord.Message) -> str:
    # !setgame <session_id> "Game Name"
    # !setgame <session_id1-session_id2> "Game Name"

    msg = message.content.replace('"', '')
    msg = msg.removeprefix('!setgame ').strip().split()
    
    session_ids = msg.pop(0).strip()
    game_name = " ".join(msg).strip()
    game,created = Game.get_or_create(name=game_name)
    
    parsed = utils.parseRange(session_ids)
    if parsed:
        a,b = parsed
    else:
        try:
            a = int(session_ids)
            b = a
        except ValueError:
            return "Invalid session ID. Please provide a valid integer or a range in the format `start-end`."
    while a <= b:
        activity = Activity.get_or_none(Activity.id == a) # type: ignore
        if not activity:
            return f"Session {a} not found."
        if activity.user != user:
            return f"Session {a} does not belong to you."
        if activity.game == game:
            return f"Session {a} is already set to game {game.name}."
        Activity.update(game=game).where(Activity.id == activity.id).execute() # type: ignore
        a += 1
    return f"Game has been set to **{game.name}** for session(s) {session_ids}."

def dm_game_info(message: discord.Message) -> str:
    # !game <game_id|game_name>
    msg = message.content.removeprefix('!game ').strip()
    try:
        gameId = int(msg)
        game = Game.get_or_none(Game.id == gameId) # type: ignore
    except ValueError:
        msg = msg.replace('"', '')
        game = Game.get_or_none(Game.name == msg)

    if game is None:
        return f"Game with ID or name '{msg}' not found."

    out = f"# {game.name}\n"
    out += f"ID: `{game.id}`\n"
    out += f"Release Year: `{game.release_year}`\n"
    out += f"Steam ID: `{game.steam_id}`\n"
    out += f"SGDB ID: `{game.sgdb_id}`\n"
    out += f"Image URL: {game.image_url}\n"
    out += f"Aliases: `{', '.join(game.aliases)}`\n"
    
    return out

def dm_search_game(msg: str) -> str:
    # !search <query>
    query = msg.removeprefix('!search ').strip()
    if not query:
        return "Please provide a search query, eg `!searchgame ocarina of time`"

    games = Game.select().where(
        (Game.name.contains(query)) |
        (Game.aliases.contains(query))
    ).order_by(Game.name).limit(50)
    if not games:
        return f"No games found matching '{query}'."

    out = "Found the following games:\n"
    for game in games:
        out += f"- `{game.id}`: {game.name}\n"
    return out

def try_expand_alias(msg: str) -> str:
    # if quotes: it should be a full title 
    if '"' in msg:
        return msg
    # if no quotes: maybe an alias?
    splitted = msg.split()
    alias = splitted[1].strip()
    game = operations.get_game_by_alias(alias)
    if game is None:
        return msg # did not find alias: return original
    # Replace alias with full game name (hax...)
    splitted[1] = f'"{game.name}"'
    msg = " ".join(splitted)
    return msg

def is_admin(user: User) -> bool:
    return str(user.id) in ADMINS

def dm_receive(message: discord.Message) -> str:
    content = utils.normalizeQuotes(message.content.strip())

    user = user_from_message(message)
    if user is None:
        logger.error("Could not get Oblivionis User for message: %s", message)
        return "ERROR: Try again later"
    
    if user.bot_commands_blocked:
        return "You are blocked from using bot commands"

    parts = content.split(" ")
    if len(parts) == 0:
        return "Could not parse message"
    first = parts[0]

    isAdmin = is_admin(user)
    if isAdmin:
        admOutput = admin_commands.adm_tree(message, user, first, content)
        if admOutput:
            return admOutput

    if first == "!help":
        return dm_help(isAdmin)
    elif first == "!game":
        content = try_expand_alias(content)
        return dm_game_info(message=message)
    elif first == "!search":
        return dm_search_game(content)
    elif first == "!add":
        content = try_expand_alias(content)
        return dm_add_session(user, content)
    elif first == "!start":
        content = try_expand_alias(content)
        return dm_start_session(user, content)
    elif first == "!stop":
        return dm_stop_session(user, message)
    elif first == "!time":
        return dm_time_session(user, message)
    elif first == "!merge":
        return dm_merge_game(user, message)
    elif first == "!remove":
        return dm_remove_session(user, message)
    elif first == "!platforms":
        platforms = Platform.select().order_by(Platform.abbreviation)
        return f"Valid platforms are: `{', '.join([p.abbreviation for p in platforms])}`"
    elif first == "!platform":
        return dm_platform(user, message)
    elif first == "!setplatform":
        return dm_set_platform(user, message)
    elif first == "!setdate":
        return dm_set_date(user, message)
    elif first == "!setgame":
        return dm_set_game(user, message)
    elif first == "!last":
        return dm_last_sessions(user, message)
    else:
        return "Unknown command. Use `!help` to see available commands."
