#! /usr/bin/env nix-shell
#! nix-shell -p rsync bash --pure -i bash --keep NIX_PATH
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

cd "$SCRIPT_PATH/../"
rm -rf template
mkdir template
rsync -a --filter=':- .gitignore' ../../development/ template/
cp ../../requirements.nix template
sed -i s#../requirements#./requirements# template/shell.nix
sed -i s#../node_modules#./node_modules# template/.eslintrc.json
rm template/server/settings/__init__.py
ln -s localhost.py template/settings/__init__.py
rm template/package.json
cp template/.gitignore template/gitignore.template
