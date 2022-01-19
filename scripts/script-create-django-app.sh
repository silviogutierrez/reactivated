#!/bin/bash
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

./packages/create-django-app/scripts/create-django-app.sh

cd testproject
nix-shell --command "pip install -e $SCRIPT_PATH/../"
nix-shell --command "python manage.py runserver"
