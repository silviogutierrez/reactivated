function super_cwd() {
    cwd_with_tilde=$(dirs -0)

    # If no virtual env is activated, behave as normal.
    if [ -z ${VIRTUAL_ENV+x} ]; then
        echo "$cwd_with_tilde"
    else
        # If we are inside this path, trim it off and show just the virtualenv in parentheses.
        # shellcheck disable=SC2295
        if [ "${PWD##$PROJECT_PATH}" != "$PWD" ]; then
            root=$(dirname "$PROJECT_PATH")
            echo "(${PWD/$root\//})"
        else
            # Else show the normal behavior but also highlight the virtualenv.
            echo "($PROJECT_NAME) $cwd_with_tilde"
        fi
    fi
}

function setup_environment() {
    set -a
    PORTS_FILE=~/.project_ports
    export PROJECT_ROOT=~/Sites

    PS1="\[\033[00m\]\u\[\033[0;33m\]@\[\033[00m\]\h\[\033[0;33m\] \$(super_cwd)\[\033[00m\]: "

    # If project path is passed in, use that. If not, try to get it from the
    # current git repository.
    #
    # There's a bug when creating a new window from inside an editable pip
    # dependency. We need to find the git project closeset to ~/Sites, as nested git projects
    # will throw this off.
    #
    # Note that if we *do* want to activate a nested nix-shell, we'd need to use
    # something like a variable that this reads once and unsets for future shells.
    # Otherwise the nested git repo will still activate the outside repo because
    # PROJECT_PATH is passed through to subshells.
    if [[ -z ${PROJECT_PATH} ]]; then
        REPOSITORY_PATH=$(git rev-parse --show-toplevel)
    else
        REPOSITORY_PATH="$PROJECT_PATH"
    fi

    WORKSPACE=$(basename "$REPOSITORY_PATH")
    PROJECT=$(basename "$(dirname "$REPOSITORY_PATH")")
    NAMESPACE_PATH=$(dirname "$(dirname "$REPOSITORY_PATH")")
    NAMESPACE=$(basename "$NAMESPACE_PATH")
    PROJECT_SLUG="${PROJECT//\./-}"
    PROJECT_NAME="$NAMESPACE-${PROJECT_SLUG}-${WORKSPACE}"
    PROJECT_PATH="$HOME/Sites/$NAMESPACE/$PROJECT/$WORKSPACE"
    VIRTUAL_ENV=$PROJECT_PATH/.venv
    PATH=$VIRTUAL_ENV/bin:$PATH
    export ENTRYPOINT=$WORKSPACE.$PROJECT.$NAMESPACE.localhost

    touch $PORTS_FILE
    DEBUG_PORT=$( (grep "$PROJECT_NAME" ~/.project_ports || true) | cut -d ' ' -f 2)

    if [ -z "$DEBUG_PORT" ]; then
        DEBUG_PORT=$((2000 + RANDOM % 65000))
        echo "$PROJECT_NAME $DEBUG_PORT" >>$PORTS_FILE
    fi
    export PGPORT=$((DEBUG_PORT + 1))
    export DATABASE_NAME="$PROJECT_NAME"

    if [ ! -d "$VIRTUAL_ENV" ]; then
        virtualenv "$VIRTUAL_ENV"
    fi

    # If a setup_mondongo function exists, call it. Helpful for user-specific settings, etc.
    type setup_reactivated &>/dev/null && setup_reactivated
}

function capture_stdout_and_stderr_if_successful() {
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    RESET='\033[0m'

    set +e

    echo -n "Running $*"

    if ! OUTPUT=$("$@" 2>&1); then
        # Used by the test script as a weird way to pass around failure. There's probably
        # a better way to do this.
        # shellcheck disable=SC2034
        AT_LEAST_ONE_ERROR=1
        printf " %bFailed!%b\n" "$RED" "$RESET"
        printf '%s\n\n' "${OUTPUT}"
    else
        printf " %bSuccess!%b\n" "$GREEN" "$RESET"
    fi
    set -e
}

function open_browser() {
    PORT=$((DEBUG_PORT + 200))
    open http://"$ENTRYPOINT":$PORT/
}

function create_fix() {
    TITLE=$1

    if [[ -z ${TITLE} ]]; then
        echo "You must pass in a PR title"
        return
    fi

    gh pr create -l automerge -b '' -t "$TITLE"
}

function start_database() {
    POSTGRESQL_DATA="$VIRTUAL_ENV/postgresql"
    pg_ctl -D "$POSTGRESQL_DATA" stop || true
    rm -rf "$POSTGRESQL_DATA"
    initdb "$POSTGRESQL_DATA"
    pg_ctl -D "$POSTGRESQL_DATA" start
}

function sync_template() {
    local SCRIPT_PATH
    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
    local PROJECT_PATH
    PROJECT_PATH="$SCRIPT_PATH/.."
    cp "$PROJECT_PATH/packages/create-django-app/template/shell.nix" shell.nix
    cp "$PROJECT_PATH/packages/create-django-app/template/Dockerfile" Dockerfile
    cp "$PROJECT_PATH/packages/create-django-app/template/requirements.txt" requirements.txt
    cp "$PROJECT_PATH/packages/create-django-app/template/server/settings/localhost.py" server/settings/localhost.py
    cp -RT "$PROJECT_PATH/packages/create-django-app/template/client" client
    cp -RT "$PROJECT_PATH/packages/create-django-app/template/server/example" server/example
}
