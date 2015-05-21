#!/bin/bash
echo Content-type: text/plain
echo

PROJECT=/var/www/embedhawk.klokantech.com
cd $PROJECT

echo $PWD
whoami

git pull

docker-compose stop
docker-compose build
docker-compose up --no-build

echo DONE
