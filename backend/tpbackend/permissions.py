PERMISSION_ADMIN = "admin"  # can use admin commands
PERMISSION_COMMANDS = "commands"  # can use commands
PERMISSION_DEVELOPER = "developer"  # can use bot that is in dev mode
PERMISSION_MANUAL_ACTIVITY = "manual_activity"  # user can do manual activity
PERMISSION_OBLIVIONIS_SYNC = (
    "oblivionis_sync"  # users activity gets synced from oblivionis
)

# new users get these
DEFAULT_PERMISSIONS = [
    PERMISSION_COMMANDS,
    PERMISSION_MANUAL_ACTIVITY,
    PERMISSION_OBLIVIONIS_SYNC,
]

ALL_PERMISSIONS = [
    PERMISSION_ADMIN,
    PERMISSION_COMMANDS,
    PERMISSION_DEVELOPER,
    PERMISSION_MANUAL_ACTIVITY,
    PERMISSION_OBLIVIONIS_SYNC,
]
