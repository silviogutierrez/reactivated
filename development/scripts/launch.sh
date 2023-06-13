#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -e

# Ensure we are logged in.
(flyctl auth whoami &>/dev/null) || (echo "You must first login with 'flyctl auth login' and try again" && exit 1)

clean_up() {
    ARG=$?
    echo "There was a problem launching your app. Remove fly.toml and try again. Be sure to visit your fly.io dashboard to remove any created instances."
    exit $ARG
}
trap clean_up ERR

SECRET_KEY=$(base64 /dev/urandom | head -c50)

DATABASE_PASSWORD=$(base64 /dev/urandom | head -c20)

flyctl launch --generate-name --region iad --no-deploy --dockerfile Dockerfile

cat <<EOF >>fly.toml

[[statics]]
  guest_path = "/app/collected"
  url_prefix = "/static"
EOF

APP_NAME=$(flyctl status --json | jq .Name -r)
URL="https://$APP_NAME.fly.dev"
CLUSTER_NAME="$APP_NAME-postgres"

flyctl postgres create --password "$DATABASE_PASSWORD" --name "$CLUSTER_NAME" --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 10
# SSH/SSL connectivity issues with first-time user accounts after creating database.
flyctl ssh establish personal override

# shellcheck disable=SC2015
for _ in 1 2 3 4 5 6 7 8 9 10; do flyctl postgres attach "$CLUSTER_NAME" && break || sleep 30; done

flyctl secrets set "SECRET_KEY=$SECRET_KEY"
flyctl deploy --remote-only

# TODO: how can we make this idempotent?
# TODO: also it takes some time to propagate.
# TODO: do we need this too? thanks to the retry above it seems to be fine.
# flyctl ssh establish personal override
# sleep 30
flyctl ssh console --command "sh /migrate.sh"

# shellcheck disable=SC2015
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s "$URL" >/dev/null && break || sleep 30; done

echo ""
echo "All done."
echo "You can visit your site by going to $URL"
echo ""
echo "Do not forget to store your root credentials for the database cluster."
echo "Username: postgres"
echo "Password: $DATABASE_PASSWORD"
echo ""
echo "It cannot be retrieved after this."
