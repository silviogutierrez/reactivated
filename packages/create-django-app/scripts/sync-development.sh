#! /usr/bin/env nix-shell
#! nix-shell -p rsync bash --pure -i bash
set -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

cd "$SCRIPT_PATH/../"
rm -rf template
mkdir template
rsync -a --filter=':- .gitignore' ../../development/ template/
rm template/server/settings/__init__.py
rm template/package.json
rm template/yarn.lock
cp template/.gitignore template/gitignore.template
