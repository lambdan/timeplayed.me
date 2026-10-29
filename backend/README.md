Originally forked from [Hamuko/oblivionis](https://github.com/Hamuko/oblivionis) but has very little in common anymore.

## Env variables

| Key                | Default    | Notes                                                                                                                  |
| ------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| LOGLEVEL           | INFO       |                                                                                                                        |
| REDIS_HOST         | localhost  |                                                                                                                        |
| REDIS_PORT         | 6379       |                                                                                                                        |
| DB_HOST            | postgres   |                                                                                                                        |
| DB_USER            |            |                                                                                                                        |
| DB_PASSWORD        |            |                                                                                                                        |
| TIMEPLAYED_DB      | storage_v2 | DB that this thing is using                                                                                            |
| DISCORD_TOKEN      |            | Discord bot is enabled if set                                                                                          |
| SGDB_TOKEN         |            | SteamGridDB is enabled if set                                                                                          |
| IGDB_CLIENT_ID     |            | IGDB is enabled if both client ID and secret are set                                                                   |
| IGDB_CLIENT_SECRET |            |                                                                                                                        |
| OBLIVIONIS_DB      |            | DB that oblivionis is using. Oblivionis sync is enabled if set                                                         |
| TIMEPLAYED_URL     |            | Base URL of the site (e.g. https://timeplayed.me). Used to link to game pages in bot commands. Leave empty to disable. |

# Tests

- `make test`: unit tests in `tpbackend/` (`*_test.py`), no dependencies.
- `make e2e`: e2e tests in `e2e/`. Spins up a fresh postgres and the backend (without Discord, SGDB and IGDB) in docker, runs the tests against the API, then tears everything down. Use `make e2e-up`, `pytest e2e` and `make e2e-down` to iterate without restarting every time.

# Fresh database

`evolutions/` only contains migrations from older schemas, so a fresh install starts from `evolutions/baseline-<n>.sql` (full schema as of evolution `n`), then applies evolutions numbered higher than `n`. `e2e/init-db.sh` does exactly that and can be mounted in `/docker-entrypoint-initdb.d` of the postgres image.

When adding a new evolution, nothing needs to change, it gets applied on top of the baseline. The baseline can be regenerated at some point with `pg_dump --schema-only --no-owner --no-privileges` and renamed to the newest evolution number.

# Restore backup

1. Get access to sql file in the psql container somehow
2. Drop and recreate the database `storage_v2` in the psql container
3. Run inside psql container: `psql -U user -d storage_v2 -f /path/to/backup_storage_v2.sql`
