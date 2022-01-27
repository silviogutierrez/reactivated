#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -e

# Ensure we are logged in.
(fly auth whoami &> /dev/null) || (echo "You must first login with 'fly auth login' and try again" && exit 1)

SECRET_KEY=$(base64 /dev/urandom | head -c50)

fly launch --generate-name --region iad --no-deploy
APP_NAME=$(fly info --json | jq .App.Name -r)
CLUSTER_NAME="$APP_NAME-postgres"

fly postgres create --name "$CLUSTER_NAME" --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 10
fly postgres attach --postgres-app "$CLUSTER_NAME"

fly secrets set "SECRET_KEY=$SECRET_KEY"
fly deploy --remote-only

# TODO: how can we make this idempotent?
# TODO: also it takes some time to propagate.
fly ssh establish personal override
sleep 30
fly ssh console --command "sh migrate.sh"
