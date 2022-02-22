#! /usr/bin/env nix-shell
#! nix-shell -p nix cacert bash --pure -i bash
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

./packages/create-django-app/scripts/sync-development.sh
./packages/create-django-app/scripts/create-django-app.sh "$PROJECT_NAME"

# TODO: why does this produce git not found?
nix-shell --command "rm -rf $PROJECT_NAME/node_modules/reactivated/* && yarn --cwd packages/reactivated tsc --outDir ../../$PROJECT_NAME/node_modules/reactivated"

cd "$PROJECT_NAME"
nix-shell --command "pip install -e $SCRIPT_PATH/../"
