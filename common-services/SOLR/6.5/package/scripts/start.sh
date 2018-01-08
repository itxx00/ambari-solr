#!/bin/bash

SOLR_PATH=$1
LOGFILE=$2
PID_FILE=$3
START_PATH=$4
PID_DIR=$(dirname "$PID_FILE")
[ -d "$PID_DIR" ] || mkdir -p $PID_DIR

if ! [ -f "$PID_FILE" ]; then
    cd $START_PATH
    echo "Starting Solr..."
    ./solr start >> $LOGFILE 2>&1 &
    echo $! >$PID_FILE
fi
