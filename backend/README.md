Originally forked from [Hamuko/oblivionis](https://github.com/Hamuko/oblivionis) but has very little in common anymore.

## Env variables

| Key                | Default    | Notes                                       |
| ------------------ | ---------- | ------------------------------------------- |
| LOGLEVEL           | INFO       |                                             |
| CACHE_MAX          | 1000       |                                             |
| ADMINS             |            | Discord user IDs of admins, comma separated |
| REDIS_HOST         | localhost  |                                             |
| REDIS_PORT         | 6379       |                                             |
| DB_HOST            | postgres   |                                             |
| DB_USER            |            |                                             |
| DB_PASSWORD        |            |                                             |
| DB_NAME            | oblivion   | DB that oblivionis is using                 |
| DB_NAME_TIMEPLAYED | storage_v2 | DB that this thing is using                 |
| DISCORD_TOKEN      |            |                                             |
| SGDB_TOKEN         |            |                                             |

# Restore backup

1. Get access to sql file in the psql container somehow
2. Drop and recreate the database `storage_v2` in the psql container
3. Run inside psql container: `psql -U user -d storage_v2 -f /path/to/backup_storage_v2.sql`
