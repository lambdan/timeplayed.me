#!/bin/sh
set -e
docker build --progress plain -t tpbackend:latest .

docker compose up -d 

docker compose logs -f 
