#!/bin/bash

set -e

PWD=$(pwd)

# https://stackoverflow.com/a/246128
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT=$(realpath "$SCRIPT_PATH/../")

ALL=0
REMOTES=$(git remote)

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --file)
        SPECIFIC_FILE="$2"
        shift
        ;;
    --all) ALL=1 ;;
    *)
        echo "Unknown parameter passed: $1"
        exit 1
        ;;
    esac
    shift
done

if [[ $ALL -eq 1 ]]; then
    echo "Running against all git files"
    CHANGED_FILES=$(git ls-files)
elif [[ $REMOTES == "" ]]; then
    echo "No origin, running against all git files"
    CHANGED_FILES=$(git ls-files)
elif [ -f "$SPECIFIC_FILE" ]; then
    echo "Specific file run: running against $SPECIFIC_FILE"
    CHANGED_FILES=$SPECIFIC_FILE
elif [ -z "$ORIGIN" ]; then
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

    # Changed files against target branch, but exclude deleted files.
    target_ref=$(git merge-base "$TARGET_BRANCH" HEAD)
    CHANGED_FILES=$(git diff --name-only --diff-filter d --relative "$target_ref")
    CHANGED_FILES=${CHANGED_FILES// /}
else
    echo "Invalid fix options"
    exit 1
fi

CHANGED_PY_FILES=$(echo "$CHANGED_FILES" | grep -e '.pyi\?$' || true)
CHANGED_PRETTIER_FILES=$(echo "$CHANGED_FILES" | grep -e '.jsx\?$\|.tsx\?$\|.yaml$\|.json$\|.md$' || true)
CHANGED_TS_JS_FILES=$(echo "$CHANGED_FILES" | grep -e '.jsx\?$\|.tsx\?$' || true)
CHANGED_SH_FILES=$(echo "$CHANGED_FILES" | grep -e '.sh$' || true)
CHANGED_NIX_FILES=$(echo "$CHANGED_FILES" | grep -e '.nix$' || true)
CHANGED_TF_FILES=$(echo "$CHANGED_FILES" | grep -e '.tf$\|.tfvars$' || true)

echo -e "[Python]:\n$CHANGED_PY_FILES\n"
echo -e "[Prettier]:\n$CHANGED_PRETTIER_FILES\n"
echo -e "[TypeScript/JS]:\n$CHANGED_TS_JS_FILES\n"
echo -e "[Shell]:\n$CHANGED_SH_FILES\n"
echo -e "[Nix]:\n${CHANGED_NIX_FILES}\n"
echo -e "[Terraform]:\n${CHANGED_TF_FILES}\n"

cd "$PROJECT_ROOT"

if [[ -n "${CHANGED_PY_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    autoflake --exclude node_modules,.venv -i -r --remove-all-unused-imports $CHANGED_PY_FILES

    # shellcheck disable=SC2086
    isort $CHANGED_PY_FILES

    # shellcheck disable=SC2086
    black $CHANGED_PY_FILES
fi

if [[ -n "${CHANGED_TS_JS_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    npm exec eslint -- --fix $CHANGED_TS_JS_FILES || true
fi

if [[ -n "${CHANGED_PRETTIER_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    npm exec prettier -- --ignore-path .gitignore $CHANGED_PRETTIER_FILES --write
fi

if [[ -n "${CHANGED_SH_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    SHELLCHECK_DIFF=$(shellcheck -x -f diff $CHANGED_SH_FILES || true)

    if [[ -n "${SHELLCHECK_DIFF// /}" ]]; then
        echo "$SHELLCHECK_DIFF" | git apply
    fi

    # shellcheck disable=SC2086
    shfmt -w $CHANGED_SH_FILES
fi

if [[ -n "${CHANGED_NIX_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    nixfmt $CHANGED_NIX_FILES
fi

if [[ -n "${CHANGED_TF_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    terraform fmt -recursive $PROJECT_ROOT
fi

cd "$PWD"
