# Image Embedding Service (IES)

[![Build Status](https://travis-ci.org/klokantech/hawk.svg?branch=master)](https://travis-ci.org/klokantech/hawk/branches)

Online service providing images hosted in Europeana portal via IIIF protocol (http://iiif.io). Developed in cooperation with Kennisland as part of Europeana Creative.

Planned architecture is described in the [wiki](https://github.com/klokantech/hawk/wiki)

![europeana-embedding-service-diagram](https://cloud.githubusercontent.com/assets/59284/6038291/fa652f0a-ac5b-11e4-8a1a-88f91ba5c2b3.jpg)

Embedding application can be run by docker-compose. This application consists of four docker containers:

* redis - which serves as local database
* nginx - which serves as proxy for embedding application itself
* embed - which is a flask application which has specified functionality there: https://github.com/klokantech/hawk/wiki/B.Embed
* ingest - which runs celery instance for downloading, compressing and uploading images to S3

Everything can be setup from one place - from the file docker-compose.yml

After the configuration (which is discussed in this file and in the README for every docker container) whole embedding app can be run from this folder via `docker-compose up` command

*Steps to run embed application*

1. Create folder for source code on some EC2 machine
2. Clone this git repository into previously created folder
3. Configure `docker-compose.yml`, fill your AWS credentials and set S3 bucket and Cloud Search domain with correct information
4. Create data folder with `sql` subfolder in current folder
5. Run script 'db_sql_create.py' which create sqlite database which is primary used as backup database to redis
6. Run `docker-compose up` command
