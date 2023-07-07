# This script is meant to be sourced, not run in a subshell.
SOURCE_DATE_EPOCH=$(date +%s)
export SOURCE_DATE_EPOCH
VIRTUAL_ENV=$PWD/.venv
PATH=$VIRTUAL_ENV/bin:$PATH
POSTGRESQL_DATA="$VIRTUAL_ENV/postgresql"
POSTGRESQL_LOGS="$VIRTUAL_ENV/postgresql/logs.txt"

# On MacOS, people may run this in /tmp which is actually /private/tmp.
# To prevent issues with the hash changing for $VIRTUAL_ENV depending on
# $PWD returning /tmp or /private/tmp, we resolve with readlink.
TMP_ENV="$TMPDIR/reactivated/$(readlink -f "$VIRTUAL_ENV" | md5sum | awk '{print $1}')"

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
    virtualenv "$VIRTUAL_ENV"
    mkdir "$VIRTUAL_ENV/static"
    pip install -r requirements.txt
fi

if [ ! -d "$POSTGRESQL_DATA" ]; then
    initdb "$POSTGRESQL_DATA"
    NEED_DATABASE=true
fi

mkdir -p "$TMP_ENV"

if [ ! -f "$EXTERNAL_PID" ]; then
    pg_ctl -o "-p 1 -k \"$PGHOST\" -c listen_addresses=\"\" -c external_pid_file=\"$EXTERNAL_PID\"" -D "$POSTGRESQL_DATA" -l "$POSTGRESQL_LOGS" start &>/dev/null
fi

if [ "$NEED_DATABASE" == true ]; then
    createdb $PGDATABASE &>/dev/null
fi
