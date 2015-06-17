import os

from celery import Celery
from flask import Flask

from models import db

def celery_factory():
	app = Flask(__name__)

	app.config.update(
		REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost')
	)

	db.init_app(app)

	task_queue = Celery(__name__, broker=app.config['REDIS_URL'], include=['app.ingest'])

	return task_queue
