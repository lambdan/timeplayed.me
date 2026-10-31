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

# Evolutions

The backend applies the database migrations in `evolutions/` when it starts. Applied ones are recorded in the `evolutions` table, so each `<n>.sql` only runs once, in order, each in its own transaction. If one fails, the backend doesn't start.

To change the schema, add the next `<n>.sql` and restart the backend.

## Upgrading from pre-automatic-evolutions

A database from before evolutions were applied automatically has no `evolutions` table, so the backend tries to apply `1.sql` (which is every evolution up to 2026-10-31), which fails on the existing tables (and is rolled back). Tell it once which evolution the database is at:

```sql
CREATE TABLE IF NOT EXISTS evolutions (id integer PRIMARY KEY, applied timestamptz NOT NULL DEFAULT now());
INSERT INTO evolutions (id) VALUES (1);
```

# Restore backup

1. Get access to sql file in the psql container somehow
2. Drop and recreate the database `storage_v2` in the psql container
3. Run inside psql container: `psql -U user -d storage_v2 -f /path/to/backup_storage_v2.sql`
