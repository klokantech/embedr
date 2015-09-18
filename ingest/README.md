The ingest docker container runs celery which is responsible for ingest each url in the batch. It downloads the item, convert it to JPG2000, push it to S3 storage and insert data about it to CloudSearch service. It shares source code with embed container. Credentials and another settings for S3 and CloudSearch can be set via docker-compose. 
The `requirements.txt` file is used during the build of the container and it specified python packages which are used by ingest application.
The `Dockerfile` is used as configuration to build docker container.
The `docker-compose-ingest.yml` is a sample of docker-compose configuration for separate ingest slave.

The sources have to be map into container itself (`/usr/local/src/hawk/`), folder for storing of actualy ingested files have to be map into `/tmp` folder in the container.

Some configuration in form of environment variables is needed to be done:
* REDIS_SERVER - base url for redis server
* REDIS_PORT_NUMBER - accessible port on the redis server
* AWS_ACCESS_KEY_ID - personal key to AWS
* AWS_SECRET_ACCESS_KEY - personal secrete key to AWS
* S3_CHUNK_SIZE - size of chunk in bytes, which can be used parallel if big images are uploaded to S3
* S3_HOST - base url of S3 server
* S3_DEFAULT_BUCKET - bucket for storing jp2 images on S3
* MAX_TASK_REPEAT - number which specifies how many times can be particular task repeated if it fails
* URL_OPEN_TIMEOUT - number in seconds which specifies how long to wait before downloading of image is started
* CLOUDSEARCH_REGION - Amazon region where the Cloud Search runs
* CLOUDSEARCH_ITEM_DOMAIN - Cloud Search domain where ingested Items are stored
* CLOUDSEARCH_BATCH_DOMAIN - Cloud Search domain where complete ingest batches are stored

*Configuration from main docker-compose*

```
ingest:
  build: ./ingest
  links:
    - redis
  volumes:
    - ./embed:/usr/local/src/hawk/
    - ./data/tmp:/tmp
  environment:
    - C_FORCE_ROOT=true
    - REDIS_SERVER=redis
    - REDIS_PORT_NUMBER=6379
    - AWS_ACCESS_KEY_ID=
    - AWS_SECRET_ACCESS_KEY=
    - S3_CHUNK_SIZE=52428800
    - S3_HOST=s3.eu-central-1.amazonaws.com
    - S3_DEFAULT_BUCKET=storage.hawk.bucket
    - MAX_TASK_REPEAT=5
    - URL_OPEN_TIMEOUT=10
    - CLOUDSEARCH_REGION=eu-central-1
    - CLOUDSEARCH_ITEM_DOMAIN=hawk
    - CLOUDSEARCH_BATCH_DOMAIN=hawk-batch
  command: bash -c "celery --app=app.task_queue.task_queue worker -E -l warning --workdir=/usr/local/src/hawk/ --autoscale=10,3 --hostname worker1.%h && celery --app=app.task_queue.task_queue worker -E -l warning --workdir=/usr/local/src/hawk/ --autoscale=10,3 --hostname worker2.%h"
```
