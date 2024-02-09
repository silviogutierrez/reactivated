#!/bin/bash

set -e
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$SCRIPT_PATH/.."
REPOSITORY_URL="https://api.github.com/repos/silviogutierrez/reactivated/branches/main/protection/required_status_checks"

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

VERSIONING="minor"

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --versioning)
        VERSIONING="$2"
        shift
        ;;
    *)
        echo "Unknown parameter passed: $1"
        exit 1
        ;;
    esac
    shift
done

echo "Current version: $CURRENT_VERSION"

python scripts/generate_types.py

npm -w reactivated run build
#
# For temporary eslint support.
sed -i '/export {};/d' packages/reactivated/dist/eslintrc.cjs

cd "${PROJECT_ROOT}/packages/reactivated/"

CURRENT_VERSION=$(jq <package.json .version -r)

if [ "$VERSIONING" != "snapshot" ]; then
    npm version --no-git-tag-version "$VERSIONING"
    NEW_VERSION=$(jq <package.json .version -r)
    SNAPSHOT_OR_RELEASE="latest"
    echo "Release version: $NEW_VERSION"
    npm publish

    cd "${PROJECT_ROOT}/packages/create-django-app/"
    npm version --no-git-tag-version --new-version "${NEW_VERSION}"
    npm publish

    cd "$PROJECT_ROOT"

    # Need to update the monorepo package-lock.json
    npm install
    git commit -am "v${NEW_VERSION}"
    git tag "v${NEW_VERSION}"

    EXISTING_CHECKS=$(disable_github_checks)
    git push
    git push --tags
    enable_github_checks "$EXISTING_CHECKS"
else
    NEW_VERSION="${CURRENT_VERSION}a${GITHUB_RUN_NUMBER}"
    SNAPSHOT_OR_RELEASE="snapshot"
    echo "Snapshot version: $NEW_VERSION"
    npm version --no-git-tag-version --new-version "${NEW_VERSION}"
    npm publish --tag cd

    cd "${PROJECT_ROOT}/packages/create-django-app/"
    npm version --no-git-tag-version --new-version "${NEW_VERSION}"
    npm publish --tag cd
    cd "$PROJECT_ROOT"
fi
echo "Published version $NEW_VERSION to NPM"

pip install wheel
python setup.py sdist bdist_wheel
twine upload dist/*
echo "Published version $NEW_VERSION to PyPI"

# Populate PyPI by forcing an install till it works.
# shellcheck disable=SC2015
for _ in 1 2 3 4 5; do pip install --ignore-installed "reactivated==$NEW_VERSION" && break || sleep 15; done

echo "::set-output name=VERSION_TAG::v$NEW_VERSION"
echo "::set-output name=SNAPSHOT_OR_RELEASE::$SNAPSHOT_OR_RELEASE"
