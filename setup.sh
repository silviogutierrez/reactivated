#!/bin/bash
set -e

# https://stackoverflow.com/a/246128
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pip install -r requirements.txt

cd packages/reactivated/
yarn

cd "$PROJECT_ROOT/sample"
yarn

start_database

cd "$PROJECT_ROOT"
