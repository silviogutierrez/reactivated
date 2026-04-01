# This script is meant to be sourced, not run in a subshell.
SOURCE_DATE_EPOCH=$(date +%s)
export SOURCE_DATE_EPOCH
export VIRTUAL_ENV=$PWD/.venv
PATH=$VIRTUAL_ENV/bin:$PATH
POSTGRESQL_DATA="$VIRTUAL_ENV/postgresql"
POSTGRESQL_LOGS="$VIRTUAL_ENV/postgresql/logs.txt"

# On MacOS, people may run this in /tmp which is actually /private/tmp.
# To prevent issues with the hash changing for $VIRTUAL_ENV depending on
# $PWD returning /tmp or /private/tmp, we resolve with readlink.
# Can't use $TMPDIR because nested nix-shell calls will put $TMPDIR in a one-off
# directory just for that shell process.
TMP_ENV="/tmp/reactivated/$(readlink -f "$VIRTUAL_ENV" | md5sum | awk '{print $1}')"

export PGPORT=1
export PGDATABASE="database"
export PGHOST=$TMP_ENV
EXTERNAL_PID="$TMP_ENV/postmaster.pid"

if [ ! -d "$VIRTUAL_ENV" ]; then
    if [ -f "$EXTERNAL_PID" ]; then
        kill -9 "$(cat "$EXTERNAL_PID")"
        rm "$EXTERNAL_PID"
    fi

    rm -rf "$TMP_ENV"
    uv venv "$VIRTUAL_ENV"
    uv sync
fi

if [ ! -d "$POSTGRESQL_DATA" ]; then
    initdb "$POSTGRESQL_DATA"

    if [ -f "$EXTERNAL_PID" ]; then
        pid_to_kill=$(cat "$EXTERNAL_PID")
        kill -9 "$pid_to_kill" &>/dev/null || echo "No PostgreSQL process to kill"
    fi

    rm -rf "$TMP_ENV"
    NEED_DATABASE=true
fi

mkdir -p "$TMP_ENV"

if ! pg_ctl status -D "$POSTGRESQL_DATA" &>/dev/null; then
    rm -f "$EXTERNAL_PID"
    pg_ctl -o "-p 1 -k \"$PGHOST\" -c listen_addresses=\"\" -c external_pid_file=\"$EXTERNAL_PID\"" -D "$POSTGRESQL_DATA" -l "$POSTGRESQL_LOGS" start &>/dev/null
fi

if [ "$NEED_DATABASE" == true ]; then
    createdb $PGDATABASE &>/dev/null
fi

export DATABASE_URL="postgres:///database?host=$TMP_ENV&port=1"
