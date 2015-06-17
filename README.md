# Image Embedding Service (IES)

Online service providing images hosted in Europeana portal via IIIF protocol (http://iiif.io). Developed in cooperation with Kennisland as part of Europeana Creative.

Planned architecture is described in the [wiki](https://github.com/klokantech/hawk/wiki)

![europeana-embedding-service-diagram](https://cloud.githubusercontent.com/assets/59284/6038291/fa652f0a-ac5b-11e4-8a1a-88f91ba5c2b3.jpg)

Embedding application can be run by docker-compose. This application consists of four docker containers:

* redis - which serves as local database
* nginx - which serves as proxy for embedding application itself
* embed - which is a flask application which has specified functionality there: https://github.com/klokantech/hawk/wiki/B.Embed
* ingest - which runs celery instance for downloading, compressing and uploading images to S3

Everything can be setup from one place - from the file docker-compose.yml

After the configuration (which will be discussed later) whole embedding app can be run from this folder via `docker-compose up` command
