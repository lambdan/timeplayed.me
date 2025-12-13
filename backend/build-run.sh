#!/bin/sh
set -e

black tpbackend

docker build --progress plain -t tpbackend:latest .

docker compose up -d 

docker compose logs -f 
