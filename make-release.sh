#!/bin/sh
set -e

BACKEND_VERSION_PATH="./backend/__version__.py"
PACKAGE_JSON_PATH="./frontend/package.json"

# check we are on correct branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "You are on branch $CURRENT_BRANCH - you can only release on main!"
  exit 1
fi

# print current version from package.json
CURRENT_VERSION=$(grep '"version":' $PACKAGE_JSON_PATH | sed -E 's/.*"version": "(.*)".*/\1/')
CURRENT_BACKEND_VERSION=$(grep '__version__' $BACKEND_VERSION_PATH | sed -E "s/.*__version__ = '(.*)'.*/\1/")
echo "Current backend version: $CURRENT_BACKEND_VERSION"
echo "Current frontend version: $CURRENT_VERSION"

# ask for new version, or leave empty to not release a new version
read -p "Enter new backend version (eg 1.2.3), or leave empty to skip backend release: " new_backend_version
read -p "Enter new frontend version (eg 1.2.3), or leave empty to skip frontend release: " new_version

NEW_BACKEND=0
NEW_FRONTEND=0

if [ -n "$new_backend_version" ]; then
  NEW_BACKEND=1
  # update version in __version__.py
  sed -i '' "s/__version__ = '.*'/__version__ = '$new_backend_version'/" $BACKEND_VERSION_PATH
fi

if [ -n "$new_version" ]; then
  NEW_FRONTEND=1
  # update version in package.json
  sed -i '' "s/\"version\": \".*\"/\"version\": \"$new_version\"/" $PACKAGE_JSON_PATH
fi

read -p "Do you want to commit the changes and create a git tag? (y/n) " answer
if [ "$answer" != "y" ]; then
  echo "Aborting release."
  exit 0
fi

GIT_MESSAGE=""

if [ $NEW_BACKEND -eq 1 ]; then
  git add $BACKEND_VERSION_PATH
  GIT_MESSAGE="Backend release: $new_backend_version"
fi

if [ $NEW_FRONTEND -eq 1 ]; then
  git add $PACKAGE_JSON_PATH
  if [ -n "$GIT_MESSAGE" ]; then
    GIT_MESSAGE="$GIT_MESSAGE, "
  fi
  GIT_MESSAGE="${GIT_MESSAGE}Frontend release: $new_version"
fi

git commit -m "$GIT_MESSAGE"

# create git tag
git tag "frontend@$new_version"
git tag "backend@$new_backend_version"

echo "Release created with tags: frontend@$new_version, backend@$new_backend_version"
