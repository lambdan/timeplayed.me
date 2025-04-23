#!/bin/sh

TAG="dev"
echo "Building and pushing version $TAG ..."

docker build -f ../Dockerfile --tag "playtime-tracker:latest" --platform linux/amd64,linux/arm64 ..
docker tag playtime-tracker:latest "davidsilverlind/playtime-tracker:$TAG"
docker push "davidsilverlind/playtime-tracker:$TAG"
