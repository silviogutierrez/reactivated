#! /usr/bin/env nix-shell
#! nix-shell -p nix cacert bash --pure -i bash
set -xe

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

DEVELOPMENT=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --name)
        PROJECT_NAME="$2"
        shift
        ;;
    --development) DEVELOPMENT=true ;;
    *)
        echo "Unknown parameter passed: $1"
        exit 1
        ;;
    esac
    shift
done

if [ -z ${PROJECT_NAME+x} ]; then
    echo "You must pass in --name"
    exit
fi

./packages/create-django-app/scripts/create-django-app.sh "$PROJECT_NAME"

nix-shell --command "rm -rf $PROJECT_NAME/node_modules/reactivated/* && yarn --cwd packages/reactivated tsc --outDir ../../$PROJECT_NAME/node_modules/reactivated"

cd "$PROJECT_NAME"
nix-shell --command "pip install -e $SCRIPT_PATH/../"
# nix-shell --command "python manage.py runserver"
nix-shell --command "python manage.py print_schema"


if [ "$DEVELOPMENT" != false ]; then
    rm -rf client
    rm -rf server/example
    ln -fs ../packages/create-django-app/template/shell.nix shell.nix
    ln -s ../packages/create-django-app/template/client client
    ln -s ../../packages/create-django-app/template/server/example server/example
    ln -fs ../../../packages/create-django-app/template/server/settings/localhost.py server/settings/localhost.py
fi
