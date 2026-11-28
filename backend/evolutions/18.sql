-- oblivionis_sync is renamed to discord_tracking: it's whether the user's Discord playtime is tracked
UPDATE "user" SET permissions = array_replace(permissions, 'oblivionis_sync', 'discord_tracking');
