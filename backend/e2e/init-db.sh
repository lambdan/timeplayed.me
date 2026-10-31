#!/bin/bash
# Initializes a fresh postgres for timeplayed.
# Runs from /docker-entrypoint-initdb.d. Only creates the database, the backend applies the evolutions.
# The oblivionis database is POSTGRES_DB, its tables are created by the backend itself.
set -euo pipefail

TP_DB="${TIMEPLAYED_DB:-storage_v2}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -c "CREATE DATABASE \"$TP_DB\";"

echo "Database $TP_DB created, the backend applies the evolutions when it starts"
