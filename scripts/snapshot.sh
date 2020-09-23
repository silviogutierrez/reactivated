#!/bin/bash

set -e

CURRENT_VERSION=$(
    cat <<EOF | python
import json
with open("packages/reactivated/package.json", "r") as package:
    version = json.load(package)["version"]
    print(version)
EOF
)

# Need jq, migrate to nix to fix this.
# CURRENT_VERSION=$(jq <packages/reactivated/package.json .version -r)

echo "Current version: $CURRENT_VERSION"
SNAPSHOT_VERSION="${CURRENT_VERSION}a${GITHUB_RUN_NUMBER}"
echo "Snapshot version: $SNAPSHOT_VERSION"

cd packages/reactivated/
yarn version --no-git-tag-version --new-version "${CURRENT_VERSION}a${GITHUB_RUN_NUMBER}"
npm publish --access public
echo "Published version $SNAPSHOT_VERSION to NPM"
cd -

scripts/build-python.sh
echo "Published version $SNAPSHOT_VERSION to PyPI"