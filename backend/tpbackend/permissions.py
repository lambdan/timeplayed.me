from enum import StrEnum


class Permission(StrEnum):
    """stored as the plain string in user.permissions"""

    ADMIN = "admin"
    COMMANDS = "commands"
    DEVELOPER = "developer"
    MANUAL_ACTIVITY = "manual_activity"
    OBLIVIONIS_SYNC = "oblivionis_sync"
    SHOW_AVATAR = "show_avatar"
    SHOW_NAME = "show_name"


DESCRIPTIONS: dict[Permission, str] = {
    Permission.ADMIN: "Can use admin commands in Discord and the admin page",
    Permission.COMMANDS: "Can use Discord bot commands",
    Permission.DEVELOPER: "Can use the bot when it runs in dev mode (commands starting with .)",
    Permission.MANUAL_ACTIVITY: "Can add activity manually (Discord commands, manual tracking page, API)",
    Permission.OBLIVIONIS_SYNC: "Oblivionis activity is synced for this user",
    Permission.SHOW_AVATAR: "Discord avatar is shown on the site (otherwise a default avatar)",
    Permission.SHOW_NAME: "Name is shown on the site (otherwise 'User <id>')",
}

# new users get these
DEFAULT_PERMISSIONS = [
    Permission.COMMANDS,
    Permission.MANUAL_ACTIVITY,
    Permission.OBLIVIONIS_SYNC,
    Permission.SHOW_AVATAR,
    Permission.SHOW_NAME,
]

ALL_PERMISSIONS = list(Permission)
