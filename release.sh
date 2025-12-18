#!/bin/bash

set -e

# Get version from argument or prompt
if [ -z "$1" ]; then
  read -p "Enter the new version (e.g. 1.0.2): " VERSION
else
  VERSION="$1"
fi

# Update version in pyproject.toml
echo "🔄 Updating version to $VERSION in pyproject.toml..."
sed -i.bak "/^\[project\]/,/^\[/ s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Build the package
echo "🔨 Building package..."
rm -rf dist/
python3 -m build

# Commit and tag
echo -e "\n\n📦 Committing and tagging v$VERSION..."
git add .
git commit -m "Release: v$VERSION"
git tag v$VERSION

# Push commit and tag
echo "🚀 Pushing to origin..."
git push origin v$VERSION
git push origin main


echo " Done! Version $VERSION has been released and is being published by GitHub Actions."

