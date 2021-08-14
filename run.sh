#!/bin/bash

PATH=$(/usr/bin/getconf PATH || /bin/kill $$)

docker stop $(docker ps -a -q --filter ancestor=rootmebot --format="{{.ID}}")
docker build -t rootmebot .
docker run -t -v `pwd`/db:/opt/db rootmebot
