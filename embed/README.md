The embed docker container runs wsgi flask embedding application. Settings for server name, some urls, etc. can be set via docker-compose. There is `supervisord.conf` which is pushed to the right place into container by docker-compose and it settup and run wsgi server itself.
The `requirements.txt` file is used during the build of the container and it specified python packages which are used by embed application.
The `Dockerfile` is used as configuration to build docker container.
The `run.py` file is a script which is run by supervisor and it starts wsgi server.
The `test.py` file is unittest script.
The `app` folder is python package with embed's application sources
The sources have to be map into container itself (`/usr/local/src/hawk/`), folder for storing of json files with orders for ingest have to be map into `/data` folder in the container.

This container have to map port 5000 to outside, then nginx can use this container as wsgi server.

Some configuration in form of environment variables is needed to be done:
* SERVER_NAME - base url for embed server
* IIIF_SERVER - base url for IIIF server
* REDIS_SERVER - base url for redis server
* REDIS_PORT_NUMBER - accessible port on the redis server
* AWS_ACCESS_KEY_ID - personal key to AWS
* AWS_SECRET_ACCESS_KEY - personal secrete key to AWS
* CLOUDSEARCH_REGION - Amazon region where the Cloud Search runs
* CLOUDSEARCH_BATCH_DOMAIN - Cloud Search domain where complete ingest batches are stored

*Configuration from docker-compose*

```
embed:
  build: ./embed
  command: /usr/local/bin/supervisord -c /etc/supervisord/supervisord.conf
  expose:
    - "5000"
  links:
    - redis
  volumes:
    - ./embed:/usr/local/src/hawk/
    - ./data/batch:/data
  environment:
    - SERVER_NAME=media.embedr.eu
    - IIIF_SERVER=iiif.embedr.eu
    - REDIS_SERVER=redis
    - REDIS_PORT_NUMBER=6379
    - AWS_ACCESS_KEY_ID=
    - AWS_SECRET_ACCESS_KEY=
    - CLOUDSEARCH_REGION=eu-central-1
    - CLOUDSEARCH_BATCH_DOMAIN=hawk-batch
```
