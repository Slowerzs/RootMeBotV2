#!/bin/bash

PATH=$(/usr/bin/getconf PATH || /bin/kill $$)

docker stop $(docker ps -a -q --filter ancestor=rootmebot --format="{{.ID}}")
docker build -t RootMeBot rootmebot --no-cache
docker run rootmebot -v `pwd`/db:/opt/RootMeBot/db 

