from enum import StrEnum


class Permission(StrEnum):
    """stored as the plain string in user.permissions"""

    ADMIN = "admin"
    COMMANDS = "commands"
    DEVELOPER = "developer"
    MANUAL_ACTIVITY = "manual_activity"
    OBLIVIONIS_SYNC = "oblivionis_sync"


DESCRIPTIONS: dict[Permission, str] = {
    Permission.ADMIN: "Can use admin commands in Discord and the admin page",
    Permission.COMMANDS: "Can use Discord bot commands",
    Permission.DEVELOPER: "Can use the bot when it runs in dev mode (commands starting with .)",
    Permission.MANUAL_ACTIVITY: "Can add activity manually (Discord commands, manual tracking page, API)",
    Permission.OBLIVIONIS_SYNC: "Oblivionis activity is synced for this user",
}

# new users get these
DEFAULT_PERMISSIONS = [
    Permission.COMMANDS,
    Permission.MANUAL_ACTIVITY,
    Permission.OBLIVIONIS_SYNC,
]

ALL_PERMISSIONS = list(Permission)
