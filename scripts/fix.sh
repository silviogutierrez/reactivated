#!/bin/bash
# set -e

PWD=$(pwd)

# https://stackoverflow.com/a/246128
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT=$(realpath "$SCRIPT_PATH/../")


cd $PROJECT_ROOT
autoflake  -i -r  --remove-all-unused-imports .
isort --recursive .
black .
cd $PWD
