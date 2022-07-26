#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -ex

npm -w create-django-app run prepublishOnly

rm -rf website_build_context
cp -R packages/create-django-app/ website_build_context
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
mv website_build_context/monorepo website_build_context/template/monorepo

sed -i s'#-e ..#./monorepo/python#' website_build_context/template/requirements.txt
# sed -i s'#../requirements#./requirements#' website_build_context/shell.nix

# cd website_build_context/

# /usr/local/bin/docker build -t testing -f website_build_context/Dockerfile website_build_context
