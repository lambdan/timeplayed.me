#!/bin/sh
set -e

BACKEND_VERSION_PATH="./backend/tpbackend/__version__.py"
PACKAGE_JSON_PATH="./frontend/package.json"

# check we are on correct branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "⚠️ You are on branch $CURRENT_BRANCH - you should probably be on main ⚠️"
  #exit 1
fi

# print current version from package.json
CURRENT_FRONTEND_VERSION=$(grep '"version":' $PACKAGE_JSON_PATH | sed -E 's/.*"version": "(.*)".*/\1/')
CURRENT_BACKEND_VERSION=$(grep '__version__' $BACKEND_VERSION_PATH | sed -E 's/.*__version__ = "(.*)".*/\1/')
echo "Current backend version: $CURRENT_BACKEND_VERSION"
echo "Current frontend version: $CURRENT_FRONTEND_VERSION"

echo
echo "Commits since last tags:"
echo "$(git log --format=%s $(git describe --tags --abbrev=0)..HEAD)"
echo

read -p "Enter new backend version (eg 1.2.3), or leave empty to skip backend release: " new_backend_version
read -p "Enter new frontend version (eg 1.2.3), or leave empty to skip frontend release: " new_frontend_version

echo "New backend: $new_backend_version"
echo "New frontend: $new_frontend_version"

NEW_BACKEND=0
NEW_FRONTEND=0

if [ -n "$new_backend_version" ]; then
  NEW_BACKEND=1
  # write new __version__.py
  echo "__version__ = \"$new_backend_version\"" > $BACKEND_VERSION_PATH
fi

if [ -n "$new_frontend_version" ]; then
  NEW_FRONTEND=1
  # update version in package.json
  sed -i '' "s/\"version\": \".*\"/\"version\": \"$new_frontend_version\"/" $PACKAGE_JSON_PATH
fi

if [ $NEW_BACKEND -eq 0 ] && [ $NEW_FRONTEND -eq 0 ]; then
  echo "No new version specified, aborting release."
  exit 0
fi

read -p "Final chance to backout, do you want to release? (y/n) " answer
if [ "$answer" != "y" ]; then
  echo "Aborting release."
  exit 0
fi

COMMIT_MESSAGE="Release"

if [ $NEW_BACKEND -eq 1 ]; then
  echo "New backend version: $new_backend_version"
  git add $BACKEND_VERSION_PATH
  COMMIT_MESSAGE="$COMMIT_MESSAGE backend@$new_backend_version"
fi

if [ $NEW_FRONTEND -eq 1 ]; then
  echo "New frontend version: $new_frontend_version"
  git add $PACKAGE_JSON_PATH
  COMMIT_MESSAGE="$COMMIT_MESSAGE frontend@$new_frontend_version"
fi

echo "Commiting..."
git commit -m "$COMMIT_MESSAGE"

# create git tag
if [ $NEW_FRONTEND -eq 1 ]; then
  TAG="frontend@$new_frontend_version"
  echo "Tagging $TAG"
  git tag "$TAG"
fi

if [ $NEW_BACKEND -eq 1 ]; then
  TAG="backend@$new_backend_version"
  echo "Tagging $TAG"
  git tag "$TAG"
fi

echo "Done! Remember to push (and the tags!)"
