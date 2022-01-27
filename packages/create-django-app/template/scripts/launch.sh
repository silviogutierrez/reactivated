#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -e

# fly postgres create and get name and password somehow.
SECRET_KEY=$(base64 /dev/urandom | head -c50)

fly launch --generate-name --region iad --no-deploy
fly secrets set "SECRET_KEY=$SECRET_KEY"
fly postgres attach  --postgres-app long-cloud-3126
fly deploy --remote-only

# TODO: how can we make this idempootent?
# TODO: also it takes some time to propgate.
fly ssh establish personal override
sleep 30
fly ssh console --command "sh migrate.sh"
