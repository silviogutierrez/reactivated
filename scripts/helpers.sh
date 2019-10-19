RED='\033[0;31m'
GREEN='\033[0;32m'
RESET='\033[0m'

function capture_stdout_and_stderr_if_successful {
    set +e
    COMMAND=$@
    printf "Running $COMMAND ... "

    OUTPUT=$($@ 2>&1)
    if [[ $? -gt 0 ]]; then
        AT_LEAST_ONE_ERROR=1
        printf "${RED}Failed!${RESET}\n"
        printf '%s\n\n' "${OUTPUT}"
    else
        printf "${GREEN}Success!${RESET}\n"
    fi
    set -e
}

function store_if_at_least_one_error {
    set +e
    $@
    [[ $? -gt 0 ]] && AT_LEAST_ONE_ERROR=1
    set -e
}

function wait_until_db_is_healthy {
    SLEEP_TIME=1
    RETRIES=0
    MAX_RETRIES=10
    until docker-compose run db mysqladmin --host=db ping; do
        if [[ $RETRIES -gt $MAX_RETRIES ]]; then
            echo "mysql never got ready after $RETRIES attempts!"
            exit 1
        fi

        echo "Waiting for mysql..."
        sleep $SLEEP_TIME
        SLEEP_TIME=$((SLEEP_TIME * 2))
        RETRIES=$((RETRIES + 1))
    done
}
