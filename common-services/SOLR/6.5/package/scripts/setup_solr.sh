#!/bin/bash

SOLR_PATH=$1
SOLR_USER=$2

echo "Starting Solr install"
getent passwd $SOLR_USER
if [ $? -eq 0 ]; then
    echo "the user exists, no need to create"
else
    echo "creating solr user"
    adduser $SOLR_USER
fi
hadoop fs -test -d /user/$SOLR_USER
if [ $? -eq 1 ]; then
    echo "Creating user dir in HDFS"
    sudo -u hdfs hdfs dfs -mkdir -p /user/$SOLR_USER
    sudo -u hdfs hdfs dfs -chown $SOLR_USER /user/solr
fi

