# Embedr: Image Embedding Service (IES)

[![Build Status](https://travis-ci.org/klokantech/hawk.svg?branch=master)](https://travis-ci.org/klokantech/hawk/branches)

Online service providing images hosted in Europeana portal via IIIF protocol (http://iiif.io). Developed in cooperation with Kennisland as part of Europeana Creative. Running on Amazon cloud infrastructure - publicly available at: http://embedr.eu/

Planned architecture is described in the [wiki](https://github.com/klokantech/hawk/wiki)

![hawk-aws-diagram-embedr](https://cloud.githubusercontent.com/assets/59284/11525883/d056901a-98d6-11e5-8317-9eebcdbe13da.jpeg)

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
4. Run `docker-compose up` command

*Alternative approach to run embed application without Nginx, Cloud Search and S3(data remains locally only)*

1. Create folder for source code on some EC2 machine
2. Clone this git repository into previously created folder
3. Run `docker-compose -f docker-compose-local.yml up` command

Embed application will be available on `http://127.0.0.1:5000/` in this case.
