#! /usr/bin/env nix-shell
#! nix-shell -p nix cacert bash python39 --pure -i bash
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

rm -rf "$SCRIPT_PATH/.venv"
python3 -m venv "$SCRIPT_PATH/.venv"

PROJECT_NAME="testproject"

"$SCRIPT_PATH/.venv/bin/pip" install Django==4.0.1
rm -rf $PROJECT_NAME
"$SCRIPT_PATH/.venv/bin/django-admin" startproject server
mv server $PROJECT_NAME
# cp "$SCRIPT_PATH/shell.nix" "$PROJECT_NAME/shell.nix"
# cp "$SCRIPT_PATH/requirements.txt" "$PROJECT_NAME/requirements.txt"
sed -i 's/parent.parent/parent.parent.parent/g' "$PROJECT_NAME/server/settings.py"
mkdir "$PROJECT_NAME/server/settings"
mv "$PROJECT_NAME/server/settings.py" "$PROJECT_NAME/server/settings/common.py"
# cp "$SCRIPT_PATH/localhost.py" "$PROJECT_NAME/server/settings/localhost.py"
ln -s  localhost.py "$PROJECT_NAME/server/settings/__init__.py"
# mkdir "$PROJECT_NAME/client"
# cp "$SCRIPT_PATH/index.tsx.template" "$PROJECT_NAME/client/index.tsx"
# cp "$SCRIPT_PATH/tsconfig.json.template" "$PROJECT_NAME/tsconfig.json"
# cp "$SCRIPT_PATH/.babelrc.json.template" "$PROJECT_NAME/.babelrc.json"
# cp "$SCRIPT_PATH/.babelrc.json.template" "$PROJECT_NAME/.babelrc.json"
cp -RT "$SCRIPT_PATH/../template" "$PROJECT_NAME"
cd "$PROJECT_NAME" || exit
nix-shell --command "yarn init --yes && yarn add reactivated@0.20.1-a641"
