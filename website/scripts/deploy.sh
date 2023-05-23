#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash --keep FLY_API_TOKEN
set -e

BUILD_ONLY=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --build-only)
        BUILD_ONLY="--build-only"
        shift
        ;;
    *) usage ;;
    esac
done

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

flyctl deploy --remote-only $BUILD_ONLY

# Currently this does not work on GitHub actions, but also is not necessary for the docs site.
# It needs to do fly console ssh issue but that fails with API auth.
# flyctl ssh console --command "sh migrate.sh"

cd ..
rm -rf website_build_context
