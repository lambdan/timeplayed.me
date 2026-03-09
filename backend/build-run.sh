#!/bin/sh
set -e

black tpbackend
make test

docker build --progress plain -t tpbackend:latest .

docker compose up -d

docker compose logs -f
