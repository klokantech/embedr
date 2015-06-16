from celery import Celery
from flask import Flask

from models import db

def celery_factory():
	app = Flask(__name__)
	app.config['REDIS_URL'] = 'redis://redis'
	db.init_app(app)

	task_queue = Celery(__name__, broker=app.config['REDIS_URL'], include=['app.ingest'])

	return task_queue
