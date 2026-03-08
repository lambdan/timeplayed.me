#!/bin/sh
set -e

PACKAGE_JSON_PATH="./frontend/package.json"

# print current version from package.json
CURRENT_VERSION=$(grep '"version":' $PACKAGE_JSON_PATH | sed -E 's/.*"version": "(.*)".*/\1/')
echo "Current version (according to $PACKAGE_JSON_PATH): $CURRENT_VERSION"

# ask for new version
read -p "Enter new version (eg 1.2.3): " new_version

# update version in package.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$new_version\"/" $PACKAGE_JSON_PATH

# commit changes
git add $PACKAGE_JSON_PATH
git commit -m "Release: $new_version"

# create git tag
git tag "$new_version"

echo "OK!"
