#! /usr/bin/env nix-shell
#! nix-shell -p jq git nix cacert bash python39 --pure -i bash --keep NIX_PATH --keep REACTIVATED_NODE --keep REACTIVATED_PYTHON --keep IS_DOCKER
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

git init --initial-branch=main

nix-shell -E '(import ./shell.nix).overrideAttrs ( oldAttrs: rec { shellHook = ""; })' --command "npm init --yes && npm pkg set type='module' && git add -A"

if [ -d "$SCRIPT_PATH/../monorepo" ]; then
    nix-shell -E '(import ./shell.nix).overrideAttrs ( oldAttrs: rec { shellHook = ""; })' --command "npm install $SCRIPT_PATH/../monorepo/node.tgz"
    nix-shell --command "pip install $SCRIPT_PATH/../monorepo/python"
else
    nix-shell -E '(import ./shell.nix).overrideAttrs ( oldAttrs: rec { shellHook = ""; })' --command "npm install -E reactivated@${CURRENT_VERSION}"
    echo "reactivated==$PIP_CURRENT_VERSION" >>requirements.txt
fi

nix-shell --command "python manage.py generate_client_assets"
nix-shell --command "python manage.py migrate"

commit_message="Initial files"

git add -A

nix-shell --command "scripts/fix.sh --all"

if [ "$HAS_GIT_CONFIGURED" = true ]; then
    git commit -am "$commit_message"
else
    git -c user.email="/dev/null@reactivated.io" -c user.name="Reactivated" commit -am "$commit_message"
fi

echo ""
echo ""
echo "All done. You can start your project by running"
echo ""
echo "cd $PROJECT_NAME"

if [ "$IS_DOCKER" = true ]; then
    echo "docker run -itp 8000:8000 -v \$PWD:/app --name $PROJECT_NAME silviogutierrez/reactivated nix-shell"
    echo "python manage.py runserver 0.0.0.0:8000"
else
    echo "nix-shell"
    echo "python manage.py runserver"
fi
