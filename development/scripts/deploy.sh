#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -e

# Ensure we are logged in.
(flyctl auth whoami &>/dev/null) || (echo "You must first login with 'flyctl auth login' and try again" && exit 1)

flyctl deploy --remote-only
flyctl ssh console --command "sh /migrate.sh"
