#!/bin/bash
set -e

# https://stackoverflow.com/a/246128
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pip install -r requirements.txt

cd "$PROJECT_ROOT/packages/reactivated/"
yarn

cd "$PROJECT_ROOT/sample"
yarn
rm -rf node_modules/reactivated/node_modules/react
rm -rf node_modules/reactivated/node_modules/react-dom

cd "$PROJECT_ROOT/packages/reactivated/"
yarn tsc --outDir "$PROJECT_ROOT/sample/node_modules/reactivated"

cd "$PROJECT_ROOT/sample"

# start_database

cd "$PROJECT_ROOT"
