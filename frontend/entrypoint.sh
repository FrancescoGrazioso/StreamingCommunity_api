#!/bin/bash

if [ ! -f "index.html" ];
then
    echo "Install webpack"
    vue init webpack .
    chmod -R 777 ./
else
    if [ ! -d "node_modules" ];
    then
        echo "Install dependencies"
        npm install
        chmod -R 777 ./
    fi
fi

exec "$@";