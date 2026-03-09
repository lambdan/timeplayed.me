#!/bin/sh
set -e

PACKAGE_JSON_PATH="./frontend/package.json"

# check we are on correct branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "You are on branch $CURRENT_BRANCH - you can only release on main!"
  exit 1
fi

# print current version from package.json
CURRENT_VERSION=$(grep '"version":' $PACKAGE_JSON_PATH | sed -E 's/.*"version": "(.*)".*/\1/')
echo "Current version (according to $PACKAGE_JSON_PATH): $CURRENT_VERSION"

# ask for new version
read -p "Enter new version (eg 1.2.3): " new_version

# confirm
read -p "You are about to release version $new_version. Are you sure? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborting release."
  exit 1
fi

# update version in package.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$new_version\"/" $PACKAGE_JSON_PATH

# commit changes
git add $PACKAGE_JSON_PATH
git commit -m "Release: $new_version"

# create git tag
git tag "$new_version"

echo "OK! Tagged $new_version"
