#!/bin/bash

set -e

PWD=$(pwd)

# https://stackoverflow.com/a/246128
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT=$(realpath "$SCRIPT_PATH/../")

SPECIFIC_FILE=$1

if [ -z "$SPECIFIC_FILE" ]; then
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

    # Changed files against target branch, but exclude deleted files.
    CHANGED_FILES=$(git diff --name-only --diff-filter d --relative "$(git merge-base $TARGET_BRANCH HEAD)")
    CHANGED_FILES=${CHANGED_FILES// /}
elif [ -f "$SPECIFIC_FILE" ]; then
    echo "Specific file run: running against $SPECIFIC_FILE"
    CHANGED_FILES=$SPECIFIC_FILE
else
    echo "Invalid file $SPECIFIC_FILE"
    exit 1
fi

CHANGED_PY_FILES=$(echo "$CHANGED_FILES" | grep -e '.pyi\?$' || true)
CHANGED_PRETTIER_FILES=$(echo "$CHANGED_FILES" | grep -e '.tsx\?$\|.yaml$\|.json$' || true)
CHANGED_SH_FILES=$(echo "$CHANGED_FILES" | grep -e '.sh$' || true)
CHANGED_NIX_FILES=$(echo "$CHANGED_FILES" | grep -e '.nix$' || true)
CHANGED_TF_FILES=$(echo "$CHANGED_FILES" | grep -e '.tf$\|.tfvars$' || true)

echo -e "[Python]:\n$CHANGED_PY_FILES\n"
echo -e "[Prettier]:\n$CHANGED_PRETTIER_FILES\n"
echo -e "[Shell]:\n$CHANGED_SH_FILES\n"
echo -e "[Nix]:\n${CHANGED_NIX_FILES}\n"
echo -e "[Terraform]:\n${CHANGED_TF_FILES}\n"

cd "$PROJECT_ROOT"

if [[ -n "${CHANGED_PY_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    autoflake --exclude node_modules,.venv -i -r --remove-all-unused-imports $CHANGED_PY_FILES

    # shellcheck disable=SC2086
    isort --recursive $CHANGED_PY_FILES

    # shellcheck disable=SC2086
    black $CHANGED_PY_FILES
fi

if [[ -n "${CHANGED_PRETTIER_FILES// /}" ]]; then
    # shellcheck disable=SC2086
    node_modules/.bin/prettier --ignore-path .gitignore $CHANGED_PRETTIER_FILES --write
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
