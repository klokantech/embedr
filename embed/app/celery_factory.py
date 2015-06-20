import os

from celery import Celery
import redis

from models import db

def celery_factory():
	REDIS_SERVER = os.getenv('REDIS_SERVER', 'localhost')
	REDIS_PORT_NUMBER = 6379
	
	db.init_db(redis.StrictRedis(host=REDIS_SERVER, port=REDIS_PORT_NUMBER, db=0))

	task_queue = Celery(__name__, broker='redis://%s' % REDIS_SERVER, include=['app.ingest'])

	return task_queue
