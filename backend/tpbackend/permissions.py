from enum import StrEnum


class Permission(StrEnum):
    """stored as the plain string in user.permissions"""

    ADMIN = "admin"
    ANONYMOUS = "anonymous"
    COMMANDS = "commands"
    DEVELOPER = "developer"
    DISCORD_TRACKING = "discord_tracking"
    FORCE_ANONYMOUS = "force_anonymous"
    HIDE_PLAYING = "hide_playing"
    MANUAL_ACTIVITY = "manual_activity"
    PRIVATE = "private"
    SHOW_NSFW = "show_nsfw"


DESCRIPTIONS: dict[Permission, str] = {
    Permission.ADMIN: "Can use admin commands in Discord and the admin page",
    Permission.ANONYMOUS: "Name, avatar and Discord ID are hidden on the site ('User <id>')",
    Permission.COMMANDS: "Can use Discord bot commands",
    Permission.DEVELOPER: "Can use the bot when it runs in dev mode (commands starting with .)",
    Permission.DISCORD_TRACKING: "Discord playtime is tracked (Oblivionis sync, now playing)",
    Permission.FORCE_ANONYMOUS: "Anonymous, and the user can't turn it off (offensive names etc)",
    Permission.HIDE_PLAYING: "Left out of now playing",
    Permission.MANUAL_ACTIVITY: "Can add activity and change its game or platform (manual tracking page, activity page, API)",
    Permission.PRIVATE: "Left out of everything public, only the user sees their own user page",
    Permission.SHOW_NSFW: "Sees NSFW game titles and covers on the site (otherwise censored)",
}

# new users get these
DEFAULT_PERMISSIONS = [
    Permission.COMMANDS,
    Permission.MANUAL_ACTIVITY,
    Permission.DISCORD_TRACKING,
]

ALL_PERMISSIONS = list(Permission)

# the user sets these on the settings page, admins set the rest
USER_SETTINGS = [
    Permission.ANONYMOUS,
    Permission.HIDE_PLAYING,
    Permission.PRIVATE,
    Permission.SHOW_NSFW,
]
