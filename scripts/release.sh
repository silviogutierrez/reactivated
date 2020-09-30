#!/bin/bash

set -e

IS_SNAPSHOT=false
VERSIONING="minor"

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --versioning)
        VERSIONING="$2"
        shift
        ;;
    --snapshot) IS_SNAPSHOT=true ;;
    *)
        echo "Unknown parameter passed: $1"
        exit 1
        ;;
    esac
    shift
done

echo "Current version: $CURRENT_VERSION"

cd packages/reactivated/

CURRENT_VERSION=$(jq <package.json .version -r)

if [ "$IS_SNAPSHOT" = false ]; then
    yarn version "--$VERSIONING"
    echo "Release version: $NEW_VERSION"
    NEW_VERSION=$(jq <package.json .version -r)
    yarn publish
    git push
    git push --tags
else
    NEW_VERSION="${CURRENT_VERSION}a${GITHUB_RUN_NUMBER}"
    echo "Snapshot version: $NEW_VERSION"
    yarn version --no-git-tag-version --new-version "${NEW_VERSION}"
    yarn publish --tag cd
fi
echo "Published version $NEW_VERSION to NPM"
cd -

pip install wheel
python setup.py sdist bdist_wheel
twine upload dist/*
echo "Published version $NEW_VERSION to PyPI"
