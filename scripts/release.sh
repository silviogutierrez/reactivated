#!/bin/bash

set -e

REPOSITORY_URL="https://api.github.com/repos/silviogutierrez/reactivated/branches/master/protection/required_status_checks"

function disable_github_checks() {
    EXISTING_CHECKS=$(curl --url $REPOSITORY_URL \
        --header "Authorization: Bearer $GITHUB_TOKEN" \
        --header 'Content-Type: application/json' |
        jq ". | {strict, contexts}" -r)

    _=$(
        curl -X PATCH --url $REPOSITORY_URL \
            --header "Authorization: Bearer $GITHUB_TOKEN" \
            --header 'Content-Type: application/json' \
            --data-binary @- <<EOF
    {
      "strict": false,
      "contexts": []
    }
EOF
    )
    echo "$EXISTING_CHECKS"
}

function enable_github_checks() {
    CHECKS_TO_ENABLE=$1
    curl -X PATCH --url $REPOSITORY_URL \
        --header "Authorization: Bearer $GITHUB_TOKEN" \
        --header 'Content-Type: application/json' \
        --data-binary "$CHECKS_TO_ENABLE"
}

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

    EXISTING_CHECKS=$(disable_github_checks)
    git push
    git push --tags
    enable_github_checks "$EXISTING_CHECKS"
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
