#!/bin/sh

docker exec playtime-tracker-postgres-1 pg_dump -U oblivion -d oblivionis |tee >"./psql_backups/$(date +"%Y-%m-%d_%H-%M-%S").sql"