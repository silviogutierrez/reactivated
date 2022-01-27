#! /usr/bin/env nix-shell
#! nix-shell ../shell.nix --pure -i bash
set -e

# Ensure we are logged in.
(fly auth whoami &> /dev/null) || (echo "You must first login with 'fly auth login' and try again" && exit 1)

fly deploy --remote-only
