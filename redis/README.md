Redis serves as fast database where only calls by ID are used. It serves as broker for celery ingest queue too. There is `redis.conf` file which is pushed into the redis docker container by docker-compose. It sets config which can't be set by runtime parameters.
It uses image `redis` from docker hub, it have to map port 6379 to outside to receive connections from embed application and celery ingest tasks workers. It uses appendonly file for persistence, so some folder from outside have to be mapped into the container ot `/data` folder.

*Configuration from docker-compose*

```
redis:
  image: redis
  ports:
    - "6379:6379"
  volumes:
    - ./data/redis:/data
    - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
  command: redis-server /usr/local/etc/redis/redis.conf --appendonly yes --no-appendfsync-on-rewrite yes
```
