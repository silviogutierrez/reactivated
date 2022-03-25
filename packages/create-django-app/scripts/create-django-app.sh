#! /usr/bin/env nix-shell
#! nix-shell -p jq git nix cacert bash python39 --pure -i bash --keep NIX_PATH --keep REACTIVATED_NODE --keep REACTIVATED_PYTHON
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
CURRENT_VERSION=$(jq <"$SCRIPT_PATH/../package.json" .version -r)
PIP_CURRENT_VERSION="${CURRENT_VERSION/-/}"

HAS_GIT_CONFIGURED=true

if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
    HAS_GIT_CONFIGURED=false
fi

PROJECT_NAME=$1

# TODO: this check doesn't actually work I don't think
if [ -z ${PROJECT_NAME+x} ]; then
    echo "You must pass in --name"
    exit
fi

cp -RT "$SCRIPT_PATH/../template" "$PROJECT_NAME"
chmod -R u+w "$PROJECT_NAME"
ln -s localhost.py "$PROJECT_NAME/server/settings/__init__.py"

cd "$PROJECT_NAME" || exit
mv gitignore.template .gitignore
sed -i "s/reactivated==\(.*\)/reactivated==$PIP_CURRENT_VERSION/" requirements.txt

if [ "$HAS_GIT_CONFIGURED" = true ]; then
    nix-shell --command "git init --initial-branch=main && git add -A"
fi

nix-shell --command "yarn init --yes && yarn add reactivated@${CURRENT_VERSION} && git add -A"

if [ -n "$REACTIVATED_NODE" ]; then
    nix-shell --command "rm -rf node_modules/reactivated && cp -R $REACTIVATED_NODE node_modules/reactivated"
    nix-shell --command "pip install -e $REACTIVATED_PYTHON"
fi

nix-shell --command "python manage.py generate_client_assets"
nix-shell --command "python manage.py migrate"
nix-shell --command "scripts/fix.sh --all"

if [ "$HAS_GIT_CONFIGURED" = true ]; then
    nix-shell --command "git add -A && git commit -m 'Initial files'"
fi

echo ""
echo ""
echo "All done. You can start your project by running"
echo ""
echo "cd $PROJECT_NAME"
echo "nix-shell"
echo "python manage.py runserver"
