#!/bin/sh

cd $(dirname $0)

ENVFILE=./predict.env

if [ -f $ENVFILE ]; then
    . $ENVFILE
    if [ $? != 0 ]; then
        echo "Failed to load environment."
        exit 1
    fi
fi

help() {
    echo "Usage: $0 [sync] [learn] [predict]"
}

sync() {
    python3 sync.py
    if [ $? != 0 ]; then
        echo "Exited, failed to sync."
        exit 1
    fi
}

summarize() {
    python3 summarize.py
    if [ $? != 0 ]; then
        echo "Exited, failed to summarize."
        exit 1
    fi
}

exprt() {
    python3 export.py
    if [ $? != 0 ]; then
        echo "Exited, failed to export."
        exit 1

    fi
}

supervise() {
    python3 supervisor.py
    if [ $? != 0 ]; then
        echo "Exited, failed to make supervisor data."
        exit 1
    fi
}

train() {
    python3 train.py
    if [ $? != 0 ]; then
        echo "Exited, failed training."
        exit 1
    fi
}

predict() {
    python3 predict.py
    if [ $? != 0 ]; then
        echo "Exited, failed prediction."
        exit 1
    fi
}

if [ $# = 0 ]; then
    help
    exit 1
fi

while [ $# != 0 ]; do
    case $1 in
    sync)
        sync
        summarize
        exprt
        supervise
        shift 1
        ;;
    learn)
        train
        shift 1
        ;;
    predict)
        predict
        shift 1
        ;;
    *)
        help
        exit 1
    esac
done

