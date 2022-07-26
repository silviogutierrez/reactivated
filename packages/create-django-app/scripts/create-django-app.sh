#! /usr/bin/env nix-shell
#! nix-shell -p jq git nix cacert bash python39 --pure -i bash --keep NIX_PATH --keep REACTIVATED_NODE --keep REACTIVATED_PYTHON --keep IS_DOCKER
set -ex

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

nix-shell -E '(import ./shell.nix).overrideAttrs ( oldAttrs: rec { shellHook = ""; })' --command "npm init --yes && git add -A"

# if [ -n "$REACTIVATED_PYTHON" ]; then
#     nix-shell --command "pip install -e $REACTIVATED_PYTHON"
# fi

if [ -d "$SCRIPT_PATH/../template/monorepo" ]; then
    nix-shell -E '(import ./shell.nix).overrideAttrs ( oldAttrs: rec { shellHook = ""; })' --command "npm install $SCRIPT_PATH/../template/monorepo/node.tgz"
    nix-shell --command "pip install $SCRIPT_PATH/../template/monorepo/python"
fi

nix-shell --command "python manage.py generate_client_assets"
nix-shell --command "python manage.py migrate"
nix-shell --command "scripts/fix.sh --all"

commit_message="Initial files"

git add -A

if [ "$HAS_GIT_CONFIGURED" = true ]; then
    git commit -m "$commit_message"
else
    git -c user.email="/dev/null@reactivated.io" -c user.name="Reactivated" commit -m "$commit_message"
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
