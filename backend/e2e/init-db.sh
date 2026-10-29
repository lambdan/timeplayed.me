#!/bin/bash
# Initializes a fresh postgres for timeplayed.
# Runs from /docker-entrypoint-initdb.d, expects evolutions mounted at /evolutions.
# The oblivionis database is POSTGRES_DB, its tables are created by the backend itself.
set -euo pipefail

TP_DB="${TIMEPLAYED_DB:-storage_v2}"
EVOLUTIONS_DIR="${EVOLUTIONS_DIR:-/evolutions}"

psql_tp() {
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$TP_DB" "$@"
}

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -c "CREATE DATABASE \"$TP_DB\";"

baseline=$(ls "$EVOLUTIONS_DIR"/baseline-*.sql | sort -V | tail -n 1)
baseline_version=$(basename "$baseline" .sql | sed 's/^baseline-//')
echo "Applying baseline $baseline (evolution $baseline_version)"
psql_tp -q -f "$baseline"

for f in $(ls "$EVOLUTIONS_DIR" | grep -E '^[0-9]+\.sql$' | sort -n); do
	n="${f%.sql}"
	if [ "$n" -gt "$baseline_version" ]; then
		echo "Applying evolution $f"
		psql_tp -q -f "$EVOLUTIONS_DIR/$f"
	fi
done

echo "Database $TP_DB initialized"
