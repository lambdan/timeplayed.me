#!/bin/sh
set -e

# check $1 is set
if [ -z "$1" ]; then
    echo "Usage: $0 backup.sql"
    exit 1
fi

# delete existing volume
docker volume rm oblivionis-postgres


# start psql container
docker run --name psql -d -v "oblivionis-postgres:/var/lib/postgresql/data" -e POSTGRES_USER=oblivion -e POSTGRES_PASSWORD=oblivion -e POSTGRES_DB=oblivionis postgres:17.2
sleep 5

# restore
docker exec -i psql sh -c 'exec psql -U oblivion -d oblivionis' < "$1"

# stop psql container
docker rm -f psql

echo "DONE!"