#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash --keep NIX_PATH
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --name)
        PROJECT_NAME="$2"
        shift
        ;;
    esac
    shift
done

if [ -z ${PROJECT_NAME+x} ]; then
    echo "You must pass in --name"
    exit 1
fi

POSTGRES_PID_FILE="./$PROJECT_NAME/.venv/postgresql/postmaster.pid"

if [ -f "$POSTGRES_PID_FILE" ]; then
    echo "$POSTGRES_PID_FILE exists. Shutting down database"
    head -n 1 <"$POSTGRES_PID_FILE" | xargs kill -9 &>/dev/null || true
fi

REACTIVATED_NODE=$(mktemp -d -t "REACTIVATED_NODE.XXX")
REACTIVATED_PYTHON="$SCRIPT_PATH/../"

export REACTIVATED_NODE
export REACTIVATED_PYTHON

./packages/create-django-app/scripts/sync-development.sh

rm -rf packages/create-django-app/template/monorepo/
python setup.py sdist -d packages/create-django-app/template/monorepo/
mv packages/create-django-app/template/monorepo/*.tar.gz packages/create-django-app/template/monorepo/python.tar.gz
tar xzf packages/create-django-app/template/monorepo/python.tar.gz -C packages/create-django-app/template/monorepo/
rm packages/create-django-app/template/monorepo/python.tar.gz
mv packages/create-django-app/template/monorepo/* packages/create-django-app/template/monorepo/python
npm -w reactivated run build
npm -w reactivated pack --pack-destination packages/create-django-app/template/monorepo/
mv packages/create-django-app/template/monorepo/*.tgz packages/create-django-app/template/monorepo/node.tgz

./packages/create-django-app/scripts/create-django-app.sh "$PROJECT_NAME"
