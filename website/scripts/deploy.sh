#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -e

cd ..

rm -rf website_build_context
cp -R website website_build_context
cp requirements.nix website_build_context/
python setup.py sdist -d website_build_context/monorepo/
mv website_build_context/monorepo/*.tar.gz website_build_context/monorepo/python.tar.gz
tar xzf website_build_context/monorepo/python.tar.gz -C website_build_context/monorepo
rm website_build_context/monorepo/python.tar.gz
mv website_build_context/monorepo/* website_build_context/monorepo/python
npm -w reactivated run build
npm -w reactivated pack --pack-destination website_build_context/monorepo/
mv website_build_context/monorepo/*.tgz website_build_context/monorepo/node.tgz
cp package-lock.json website_build_context/

sed -i s'#-e ..#./monorepo/python#' website_build_context/requirements.txt
sed -i s'#../requirements#./requirements#' website_build_context/shell.nix

cd website_build_context/

# Ensure we are logged in.
(flyctl auth whoami &>/dev/null) || (echo "You must first login with 'flyctl auth login' and try again" && exit 1)

flyctl deploy --remote-only
flyctl ssh console --command "sh migrate.sh"

cd ..
rm -rf website_build_context
