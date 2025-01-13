#!/bin/bash

set -e

PWD=$(pwd)

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT=$(realpath "$SCRIPT_PATH/..")

SERVER=1
CLIENT=1
E2E=1
BENCHMARK=1
INFRASTRUCTURE=1
ALL=0
REMOTES=$(git remote)

# shellcheck source=SCRIPTDIR/helpers.sh
source "$SCRIPT_PATH/helpers.sh"
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --all)
        ALL=1
        shift
        ;;
    --server)
        SERVER=1
        CLIENT=0
        E2E=0
        BENCHMARK=0
        INFRASTRUCTURE=0
        shift
        ;;
    --client)
        SERVER=0
        CLIENT=1
        E2E=0
        BENCHMARK=0
        INFRASTRUCTURE=0
        shift
        ;;
    --e2e)
        SERVER=0
        CLIENT=0
        E2E=1
        BENCHMARK=0
        INFRASTRUCTURE=0
        shift
        ;;
    --benchmark)
        SERVER=0
        CLIENT=0
        E2E=0
        BENCHMARK=1
        INFRASTRUCTURE=0
        shift
        ;;
    --infrastructure)
        SERVER=0
        CLIENT=0
        E2E=0=
        BENCHMARK=0
        INFRASTRUCTURE=1
        shift
        ;;
    *) usage ;;
    esac
done

echo "$CLIENT $E2E $BENCHMARK" >/dev/null

AT_LEAST_ONE_ERROR=0

if [[ $ALL -eq 1 ]] || [[ $REMOTES == "" ]]; then
    CHANGED_FILES=$(git ls-files)
else
    if [ "$GITHUB_BASE_REF" != "" ]; then
        TARGET_BRANCH="origin/$GITHUB_BASE_REF"
        echo "PR event: running against base branch $TARGET_BRANCH"
    elif [ "$GITHUB_EVENT_NAME" = "push" ]; then
        TARGET_BRANCH=$(git rev-parse HEAD~1)
        echo "Push event: running against previous commit $TARGET_BRANCH"
    else
        TARGET_BRANCH="origin/main"
        echo "Local run: running against default branch $TARGET_BRANCH"
    fi
    target_ref=$(git merge-base "$TARGET_BRANCH" HEAD)
    CHANGED_FILES=$(git diff --name-only --diff-filter d --relative "$target_ref")
fi

CHANGED_TS_JS_FILES=$(echo "$CHANGED_FILES" | grep -e '.jsx\?$\|.tsx\?$' || true)

cd "$PROJECT_ROOT"

if [[ $SERVER -eq 1 ]]; then
    capture_stdout_and_stderr_if_successful pytest
    capture_stdout_and_stderr_if_successful flake8 .
    capture_stdout_and_stderr_if_successful isort -c .
    capture_stdout_and_stderr_if_successful black . --check
    capture_stdout_and_stderr_if_successful mypy --no-incremental .
    capture_stdout_and_stderr_if_successful python manage.py makemigrations --dry-run --check
fi

if [[ $CLIENT -eq 1 ]]; then
    # capture_stdout_and_stderr_if_successful npm exec jest

    if [[ -n "${CHANGED_TS_JS_FILES// /}" ]]; then
        # shellcheck disable=SC2086
        capture_stdout_and_stderr_if_successful npm exec eslint -- $CHANGED_TS_JS_FILES
    fi
    capture_stdout_and_stderr_if_successful npm exec prettier -- --ignore-path .gitignore --check '**/*.{js,jsx,ts,tsx,yaml,json,md}'
    capture_stdout_and_stderr_if_successful npm exec tsc
fi

if [[ $INFRASTRUCTURE -eq 1 ]]; then
    CHANGED_NIX_FILES=$(echo "$CHANGED_FILES" | grep -e '.nix$' || true)
    CHANGED_SH_FILES=$(echo "$CHANGED_FILES" | grep -e '.sh$' || true)

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
fi

cd "$PWD"

exit $AT_LEAST_ONE_ERROR
