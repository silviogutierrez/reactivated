# This script is meant to be sourced, not run in a subshell.
set -e

SOURCE_DATE_EPOCH=$(date +%s)
export SOURCE_DATE_EPOCH
VIRTUAL_ENV=$PWD/.venv
PATH=$VIRTUAL_ENV/bin:$PATH
POSTGRESQL_DATA="$VIRTUAL_ENV/postgresql"
POSTGRESQL_LOGS="$VIRTUAL_ENV/postgresql/logs.txt"
TMP_ENV="$TMPDIR/reactivated/$(echo "$VIRTUAL_ENV" | md5sum | awk '{print $1}')"

export PGPORT=1
export PGDATABASE="database"
export PGHOST=$TMP_ENV
EXTERNAL_PID="$TMP_ENV/postmaster.pid"

if [ ! -d "$VIRTUAL_ENV" ]; then
    if [ -f "$EXTERNAL_PID" ]; then
        kill -9 "$(cat "$EXTERNAL_PID")"
        rm "$EXTERNAL_PID"
    fi

    NEED_DATABASE=true
    yarn
    rm -rf "$TMP_ENV"
    virtualenv "$VIRTUAL_ENV"
    mkdir "$VIRTUAL_ENV/static"
    # Impure nix shell has issues with this on international systems since LANG
    # might be set.
    LANG=en_US.UTF-8 initdb "$POSTGRESQL_DATA"
    pip install -r requirements.txt

fi

set +e

mkdir -p "$TMP_ENV"

if [ ! -f "$EXTERNAL_PID" ]; then
    pg_ctl -o "-p 1 -k \"$PGHOST\" -c listen_addresses=\"\" -c external_pid_file=\"$EXTERNAL_PID\"" -D "$POSTGRESQL_DATA" -l "$POSTGRESQL_LOGS" start &>/dev/null
fi

if [ "$NEED_DATABASE" == true ]; then
    createdb $PGDATABASE &>/dev/null
fi
