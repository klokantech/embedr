Nginx web server works as a proxy for uwsgi flask embed application. It ads security to /ingest too. There is embedhawk.conf file which is pushed into the nginx container by docker-compose. 
Create .htpasswd file with credenitials for ingest and copy it with docker-compose to /etc/nginx/.htpasswd into this docker container.

