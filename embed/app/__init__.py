"""Module which provides flask aplication factory"""

import os

from flask import Flask
import redis

from app import views
from models import db


def app_factory(db_backend=None):
	app = Flask(__name__)

	app.config.update(
		SERVER_NAME=os.getenv('SERVER_NAME', '127.0.0.1:5000'),
		IIIF_SERVER=os.getenv('IIIF_SERVER', '127.0.0.1'),
		REDIS_SERVER=os.getenv('REDIS_SERVER', 'localhost'),
		REDIS_PORT_NUMBER=int(os.getenv('REDIS_PORT_NUMBER', 6379)),
		DEBUG=os.getenv('DEBUG', False),
		HOST=os.getenv('HOST', '127.0.0.1'),
		PORT=int(os.getenv('PORT', 5000))
	)
	
	if db_backend:
		db.init_db(db_backend)
	else:
		db.init_db(redis.StrictRedis(host=app.config['REDIS_SERVER'], port=app.config['REDIS_PORT_NUMBER'], db=0))

	if not hasattr(app, 'extensions'):
		app.extensions = dict()

	if 'redis' in app.extensions:
		raise ValueError('Already registered config prefix "redis"')
	
	app.extensions['redis'] = db

	app.route('/')(views.index)
	app.route('/<unique_id>')(views.iFrame)
	app.route('/<unique_id>/<order>')(views.iFrame)
	app.route('/<unique_id>/manifest.json')(views.iiifMeta)
	app.route('/oembed', methods=['GET'])(views.oEmbed)
	app.route('/ingest', methods=['GET', 'POST'])(views.ingest)

	return app
