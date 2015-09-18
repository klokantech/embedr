Nginx web server works as a proxy for uwsgi flask embed application. It ads security to /ingest too. There is `embedhawk.conf` file with configuration for nginx which is pushed into the nginx container by docker-compose. 
Create .htpasswd file with credentials for ingest and copy it with docker-compose to /etc/nginx/.htpasswd into this docker container.
It uses image `klokantech/nginx` from docker hub, it have to map port 80 to outside to receive connections from clients. Connection to the correct url and port of the embed flask application have to be set properly too.

*Configuration from docker-compose*

```
nginx:
  image: klokantech/nginx
  ports:
    - "80:80"
  links:
    - embed
  volumes:
    - nginx/:/etc/nginx/conf.d/
    - .htpasswd:/etc/nginx/.htpasswd
```
