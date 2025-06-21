#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available

# The MIT License (MIT)
# Copyright (c) 2016 vishnubob
# https://github.com/vishnubob/wait-for-it

set -e

TIMEOUT=15
QUIET=0
HOST=""
PORT=""
CMD=("")

print_usage() {
    echo "Usage: $0 host:port [-t timeout] [-- command args]"
    echo "-h HOST | --host=HOST       Host or IP under test"
    echo "-p PORT | --port=PORT       TCP port under test"
    echo "-t TIMEOUT | --timeout=TIMEOUT  Timeout in seconds, zero for no timeout"
    echo "-- COMMAND ARGS             Execute command with args after the test finishes"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        *:* )
            HOSTPORT=(${1//:/ })
            HOST=${HOSTPORT[0]}
            PORT=${HOSTPORT[1]}
            shift 1
            ;;
        -h)
            HOST="$2"
            shift 2
            ;;
        --host=*)
            HOST="${1#*=}"
            shift 1
            ;;
        -p)
            PORT="$2"
            shift 2
            ;;
        --port=*)
            PORT="${1#*=}"
            shift 1
            ;;
        -t)
            TIMEOUT="$2"
            shift 2
            ;;
        --timeout=*)
            TIMEOUT="${1#*=}"
            shift 1
            ;;
        -q|--quiet)
            QUIET=1
            shift 1
            ;;
        --)
            shift
            CMD=("$@")
            break
            ;;
        *)
            print_usage
            ;;
    esac
done

if [[ "$HOST" == "" || "$PORT" == "" ]]; then
    print_usage
fi

if [[ $QUIET -eq 0 ]]; then
    echo "Waiting for $HOST:$PORT..."
fi

for i in $(seq $TIMEOUT); do
    nc -z $HOST $PORT > /dev/null 2>&1 && break
    sleep 1
done

if [[ $QUIET -eq 0 ]]; then
    echo "$HOST:$PORT is available!"
fi

if [[ ${#CMD[@]} -gt 0 ]]; then
    exec "${CMD[@]}"
fi 