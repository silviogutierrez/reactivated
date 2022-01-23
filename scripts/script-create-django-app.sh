#!/bin/bash
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

./packages/create-django-app/scripts/create-django-app.sh

PROJECT_NAME="testproject"

nix-shell --command "rm -rf $PROJECT_NAME/node_modules/reactivated/* && yarn --cwd packages/reactivated tsc --outDir ../../$PROJECT_NAME/node_modules/reactivated"

cd $PROJECT_NAME
nix-shell --command "pip install -e $SCRIPT_PATH/../"
# nix-shell --command "python manage.py runserver"
