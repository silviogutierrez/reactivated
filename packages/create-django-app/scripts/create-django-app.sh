#! /usr/bin/env nix-shell
#! nix-shell -p git nix cacert bash python39 --pure -i bash
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

rm -rf "$SCRIPT_PATH/.venv"
python3 -m venv "$SCRIPT_PATH/.venv"

PROJECT_NAME=$1

if [ -z ${PROJECT_NAME+x} ]; then
    echo "You must pass in --name"
    exit
fi

"$SCRIPT_PATH/.venv/bin/pip" install Django==4.0.1
# TODO: should probably not do this if the directory exists. Maybe outside?
# rm -rf "$PROJECT_NAME"
"$SCRIPT_PATH/.venv/bin/django-admin" startproject server
mv server "$PROJECT_NAME"
mkdir "$PROJECT_NAME/server/settings"
rm "$PROJECT_NAME/server/settings.py"

# TODO: remove me.
mkdir -p "$PROJECT_NAME/static"

ln -s localhost.py "$PROJECT_NAME/server/settings/__init__.py"

cp -RT "$SCRIPT_PATH/../template" "$PROJECT_NAME"
cd "$PROJECT_NAME" || exit
mv gitignore.template .gitignore
nix-shell --command "git init --initial-branch=main && git add -A"
nix-shell --command "yarn init --yes && yarn add reactivated@0.20.1-a685 && git add -A"
nix-shell --command "scripts/fix.sh --all"
nix-shell --command "git add -A && git commit -m 'Initial files'"

echo ""
echo ""
echo "All done. You can start your project by running"
echo ""
echo "cd $PROJECT_NAME"
echo "nix-shell"
echo "python manage.py runserver"
