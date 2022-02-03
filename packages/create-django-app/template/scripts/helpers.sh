function capture_stdout_and_stderr_if_successful() {
    local RED='\033[0;31m'
    local GREEN='\033[0;32m'
    local RESET='\033[0m'

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
