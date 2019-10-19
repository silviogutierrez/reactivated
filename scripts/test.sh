#!/bin/bash
# set -e

PWD=$(pwd)

# https://stackoverflow.com/a/246128
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT=$(realpath "$SCRIPT_PATH/../")

source "$SCRIPT_PATH/helpers.sh"

AT_LEAST_ONE_ERROR=0

cd $PROJECT_ROOT
# capture_stdout_and_stderr_if_successful pytest
# capture_stdout_and_stderr_if_successful black --check .
# capture_stdout_and_stderr_if_successful isort --recursive -c .
# capture_stdout_and_stderr_if_successful mypy --no-incremental .
# capture_stdout_and_stderr_if_successful packages/reactivated/node_modules/.bin/prettier --ignore-path .gitignore --check '**/*.{ts,tsx,yaml}'

cd packages/reactivated/
capture_stdout_and_stderr_if_successful node_modules/.bin/tslint -p .
cd $PWD

exit $AT_LEAST_ONE_ERROR
