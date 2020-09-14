#!/bin/bash

set -e

PWD=$(pwd)

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT=$(realpath "$SCRIPT_PATH/..")

if [ "$GITHUB_BASE_REF" != "" ]; then
    TARGET_BRANCH="origin/$GITHUB_BASE_REF"
    echo "PR event: running against base branch $TARGET_BRANCH"
elif [ "$GITHUB_EVENT_NAME" = "push" ]; then
    TARGET_BRANCH=$(git rev-parse HEAD~1)
    echo "Push event: running against previous commit $TARGET_BRANCH"
else
    TARGET_BRANCH="origin/master"
    echo "Local run: running against default branch $TARGET_BRANCH"
fi

SERVER=1
CLIENT=1
E2E=1
INFRASTRUCTURE=1

# shellcheck source=SCRIPTDIR/helpers.sh
source "$SCRIPT_PATH/helpers.sh"
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --server)
        SERVER=1
        CLIENT=0
        E2E=0
        INFRASTRUCTURE=0
        shift
        ;;
    --client)
        SERVER=0
        CLIENT=1
        E2E=0
        INFRASTRUCTURE=0
        shift
        ;;
    --e2e)
        SERVER=0
        CLIENT=0
        E2E=1
        INFRASTRUCTURE=0
        shift
        ;;
    --infrastructure)
        SERVER=0
        CLIENT=0
        E2E=0
        INFRASTRUCTURE=1
        shift
        ;;
    *) usage ;;
    esac
done

AT_LEAST_ONE_ERROR=0

cd $PROJECT_ROOT

if [[ $SERVER -eq 1 ]]; then
    capture_stdout_and_stderr_if_successful pytest
    capture_stdout_and_stderr_if_successful flake8 .
    capture_stdout_and_stderr_if_successful isort --recursive -c .
    capture_stdout_and_stderr_if_successful black . --check
    capture_stdout_and_stderr_if_successful mypy --no-incremental .
fi

if [[ $CLIENT -eq 1 ]]; then
    capture_stdout_and_stderr_if_successful node_modules/.bin/tslint -p packages/reactivated
    capture_stdout_and_stderr_if_successful node_modules/.bin/tslint -p sample
    capture_stdout_and_stderr_if_successful node_modules/.bin/prettier --ignore-path .gitignore --check '**/*.{ts,tsx,yaml,json}'
fi

if [[ $E2E -eq 1 ]]; then
    capture_stdout_and_stderr_if_successful echo "No E2E tests yet"
fi

if [[ $INFRASTRUCTURE -eq 1 ]]; then
    CHANGED_NIX_FILES=$(git diff --name-only --diff-filter d --relative "$(git merge-base $TARGET_BRANCH HEAD)" | grep -e '.nix$' || true)
    CHANGED_SH_FILES=$(git diff --name-only --diff-filter d --relative "$(git merge-base $TARGET_BRANCH HEAD)" | grep -e '.sh$' || true)

    if [[ -n "${CHANGED_SH_FILES// /}" ]]; then
        # shellcheck disable=SC2086
        capture_stdout_and_stderr_if_successful shellcheck $CHANGED_SH_FILES -x

        # shellcheck disable=SC2086
        capture_stdout_and_stderr_if_successful shfmt -d $CHANGED_SH_FILES
    fi

    if [[ -n "${CHANGED_NIX_FILES// /}" ]]; then
        # shellcheck disable=SC2086
        capture_stdout_and_stderr_if_successful nixfmt -c $CHANGED_NIX_FILES
    fi

    capture_stdout_and_stderr_if_successful terraform fmt -recursive -check
fi

cd "$PWD"

exit $AT_LEAST_ONE_ERROR
