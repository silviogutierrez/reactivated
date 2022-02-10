#! /usr/bin/env nix-shell
#! nix-shell -p jq git nix cacert bash python39 --pure -i bash
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
CURRENT_VERSION=$(jq < "$SCRIPT_PATH/../package.json" .version -r)
PIP_CURRENT_VERSION="${CURRENT_VERSION/-/}"

rm -rf "$SCRIPT_PATH/.venv"
python3 -m venv "$SCRIPT_PATH/.venv"

PROJECT_NAME=$1

if [ -z ${PROJECT_NAME+x} ]; then
    echo "You must pass in --name"
    exit
fi

cp -RT "$SCRIPT_PATH/../template" "$PROJECT_NAME"
ln -s localhost.py "$PROJECT_NAME/server/settings/__init__.py"

cd "$PROJECT_NAME" || exit
mv gitignore.template .gitignore
sed  -i "s/reactivated==\(.*\)/reactivated==$PIP_CURRENT_VERSION/" requirements.txt
nix-shell --command "git init --initial-branch=main && git add -A"
nix-shell --command "yarn init --yes && yarn add reactivated@${CURRENT_VERSION} && git add -A"
nix-shell --command "python manage.py generate_client_assets"
nix-shell --command "python manage.py migrate"
nix-shell --command "scripts/fix.sh --all"
nix-shell --command "git add -A && git commit -m 'Initial files'"

echo ""
echo ""
echo "All done. You can start your project by running"
echo ""
echo "cd $PROJECT_NAME"
echo "nix-shell"
echo "python manage.py runserver"
